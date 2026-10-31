import ipaddress
import json
import os
import secrets
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

import paramiko
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, IPvAnyAddress

load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(
    title="CyberRange - Red Team vs Blue Team",
    description="Escenario SSH controlado para laboratorio de ciberseguridad",
    version="1.1.0",
)

api_key_header = APIKeyHeader(name="X-Lab-Token", auto_error=False)
scenario_lock = Lock()


class SSHScenarioRequest(BaseModel):
    ip: IPvAnyAddress


def verificar_token(token: str | None = Security(api_key_header)):
    esperado = os.getenv("LAB_API_TOKEN", "").strip()

    if not esperado or not token or not secrets.compare_digest(token, esperado):
        raise HTTPException(status_code=401, detail="Acceso no autorizado")


def cargar_configuracion():
    ip_texto = os.getenv("LAB_TARGET_IP", "").strip()

    try:
        ip_autorizada = ipaddress.ip_address(ip_texto)
    except ValueError as error:
        raise HTTPException(
            status_code=503,
            detail="LAB_TARGET_IP no esta configurada correctamente",
        ) from error

    if not ip_autorizada.is_private:
        raise HTTPException(
            status_code=503,
            detail="El laboratorio requiere una direccion IP privada",
        )

    try:
        credenciales = json.loads(
            os.getenv("LAB_SSH_CREDENTIALS_JSON", "[]")
        )
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=503,
            detail="La configuracion JSON de credenciales es invalida",
        ) from error

    if (
        not isinstance(credenciales, list)
        or len(credenciales) != 10
        or any(
            not isinstance(par, dict)
            or not isinstance(par.get("username"), str)
            or not par["username"]
            or not isinstance(par.get("password"), str)
            or not par["password"]
            for par in credenciales
        )
    ):
        raise HTTPException(
            status_code=503,
            detail="Configura exactamente 10 pares usuario/password de laboratorio",
        )

    known_hosts = Path.home() / ".ssh" / "known_hosts"

    if not known_hosts.is_file():
        raise HTTPException(
            status_code=503,
            detail="No existe el archivo SSH known_hosts",
        )

    return str(ip_autorizada), credenciales, known_hosts


def intentar_ssh(ip, usuario, password, known_hosts):
    cliente = paramiko.SSHClient()

    try:
        cliente.load_host_keys(str(known_hosts))
        cliente.set_missing_host_key_policy(paramiko.RejectPolicy())

        cliente.connect(
            hostname=ip,
            port=22,
            username=usuario,
            password=password,
            timeout=5,
            auth_timeout=5,
            banner_timeout=5,
            allow_agent=False,
            look_for_keys=False,
        )

        return "SUCCESS"

    except paramiko.AuthenticationException:
        return "FAILED"
    except paramiko.BadHostKeyException:
        return "HOST_KEY_MISMATCH"
    except (TimeoutError, socket.timeout):
        return "TIMEOUT"
    except paramiko.SSHException:
        return "SSH_ERROR"
    except Exception:
        return "CONNECTION_ERROR"
    finally:
        cliente.close()


@app.get("/api/v1/health")
def health():
    return {
        "status": "running",
        "service": "CyberRange Red Team SSH API",
    }


@app.post("/api/v1/red-team/ssh-scenario")
def ejecutar_escenario(
    data: SSHScenarioRequest,
    _autorizado=Depends(verificar_token),
):
    ip_autorizada, credenciales, known_hosts = cargar_configuracion()

    if str(data.ip) != ip_autorizada:
        raise HTTPException(
            status_code=403,
            detail="Objetivo no autorizado para este laboratorio",
        )

    if not scenario_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=409,
            detail="Ya existe un escenario en ejecucion",
        )

    try:
        inicio = datetime.now(timezone.utc)
        reloj_inicio = time.perf_counter()

        exitosos = 0
        fallidos = 0
        errores = 0
        resultados = []

        for numero, par in enumerate(credenciales, start=1):
            timestamp = datetime.now(timezone.utc).isoformat()

            resultado = intentar_ssh(
                ip_autorizada,
                par["username"],
                par["password"],
                known_hosts,
            )

            if resultado == "SUCCESS":
                exitosos += 1
            elif resultado == "FAILED":
                fallidos += 1
            else:
                errores += 1

            resultados.append({
                "attempt": numero,
                "username": par["username"],
                "result": resultado,
                "timestamp": timestamp,
            })

            if numero < len(credenciales):
                time.sleep(1)

        return {
            "scenario": "SSH_AUTHENTICATION_TEST",
            "target": ip_autorizada,
            "start_timestamp": inicio.isoformat(),
            "end_timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(
                time.perf_counter() - reloj_inicio, 3
            ),
            "total_attempts": len(resultados),
            "successful": exitosos,
            "failed": fallidos,
            "errors": errores,
            "attempts": resultados,
        }
    finally:
        scenario_lock.release()
