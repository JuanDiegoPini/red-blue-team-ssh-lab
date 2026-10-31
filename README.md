# Red Team vs Blue Team - SSH CyberRange Lab

Laboratorio de ciberseguridad desarrollado en Python y FastAPI para simular intentos de autenticacion SSH en un entorno controlado y generar eventos observables por un equipo Blue Team.

El proyecto permite estudiar la relacion entre las acciones del Red Team y los registros de seguridad del sistema Ubuntu utilizado como objetivo.

## Objetivo

Implementar un escenario practico de Red Team vs Blue Team en el que una API coordina diez intentos de autenticacion SSH contra una maquina Ubuntu autorizada y devuelve un reporte estructurado de los resultados.

Este proyecto esta orientado a aprendizaje, simulacion y pruebas dentro de un laboratorio privado.

## Tecnologias

- Python 3.11
- FastAPI y Pydantic
- Paramiko para conexiones SSH
- python-dotenv para configuracion
- Uvicorn como servidor ASGI
- unittest y HTTPX para pruebas automatizadas

## Arquitectura

```text
Red Team
   |
   | Solicitud HTTP + token
   v
FastAPI
   |
   | Validacion de autorizacion e IP
   v
Controlador del escenario
   |
   | 10 intentos de autenticacion
   v
Ubuntu - Blue Team
   |
   | Eventos de autenticacion SSH
   v
Registros de seguridad
```

El backend devuelve el resultado de cada intento, las marcas de tiempo y un resumen de ejecucion.

## Caracteristicas

- API REST para ejecutar escenarios SSH controlados.
- Autenticacion mediante el encabezado X-Lab-Token.
- Validacion de una IP privada autorizada.
- Diez pares de credenciales de laboratorio configurables.
- Verificacion de la identidad del servidor SSH.
- Prevencion de ejecuciones simultaneas en un mismo proceso.
- Registro de intentos exitosos, fallidos y errores.
- Respuesta JSON con marcas de tiempo y duracion.
- Pruebas automatizadas sin conexiones SSH reales.

## Estructura

```text
red-blue-team-ssh-lab/
|-- main.py
|-- requirements.txt
|-- requirements-dev.txt
|-- .env.example
|-- .gitignore
|-- tests/
|   `-- test_api.py
`-- README.md
```

## Requisitos

- Windows, Linux o macOS con Python 3.11 o compatible.
- Una maquina Ubuntu propia o autorizada.
- Servidor OpenSSH habilitado en Ubuntu.
- Conectividad de red entre el equipo Red Team y Ubuntu.
- Identidad del servidor SSH verificada en known_hosts.

## Instalacion

Clona el repositorio y entra al directorio del proyecto.

En PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edita el archivo .env sin compartir sus valores privados.

Variables necesarias:

- LAB_TARGET_IP: IP privada autorizada de Ubuntu.
- LAB_API_TOKEN: token secreto para utilizar la API.
- LAB_SSH_CREDENTIALS_JSON: lista JSON de exactamente 10 objetos con username y password.

Las credenciales deben pertenecer exclusivamente al laboratorio.

Antes de ejecutar el escenario, verifica por un canal confiable la huella de la clave SSH de Ubuntu y registra esa identidad en el archivo known_hosts del usuario que ejecutara Python.

## Iniciar la API

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Documentacion interactiva local:

http://127.0.0.1:8000/docs

## Endpoints

| Metodo | Ruta | Funcion |
|---|---|---|
| GET | /api/v1/health | Consultar estado de la API |
| POST | /api/v1/red-team/ssh-scenario | Ejecutar el escenario autorizado |

El endpoint del escenario requiere el encabezado X-Lab-Token y un cuerpo JSON con la direccion IP del objetivo.

La ejecucion solo se permite cuando la IP coincide con LAB_TARGET_IP y la configuracion del laboratorio es valida.

## Resultados

La respuesta del escenario incluye:

- IP del objetivo autorizado.
- Fecha y hora de inicio y finalizacion.
- Duracion total de la ejecucion.
- Cantidad de intentos exitosos.
- Cantidad de intentos fallidos.
- Cantidad de errores.
- Resultado individual de cada intento.

Estos datos pueden contrastarse con los registros SSH del sistema Ubuntu para analizar la actividad observada por el Blue Team.

## Pruebas automatizadas

Instala las dependencias de desarrollo:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Ejecuta:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Estado verificado: 6 pruebas aprobadas.

Las pruebas utilizan simulaciones para evitar conexiones SSH reales. No sustituyen una validacion integral en el laboratorio.

## Seguridad y limitaciones

- Utiliza exclusivamente maquinas propias o autorizadas.
- No expongas esta API directamente a Internet.
- No publiques archivos .env ni credenciales SSH.
- No utilices cuentas o contrasenas de produccion.
- El objetivo debe ser una IP privada configurada previamente.
- Las claves SSH desconocidas se rechazan.
- El bloqueo de ejecuciones simultaneas funciona dentro de un mismo proceso; no es un control distribuido.
- El token de API debe mantenerse privado.
- La herramienta no reemplaza una plataforma completa de gestion de CyberRange.

## Estado

Version de portafolio de un laboratorio Red Team vs Blue Team.

Funcionalidades implementadas y seis pruebas automatizadas aprobadas. Pendiente validacion integral con la infraestructura SSH y los registros del Blue Team.

## Uso responsable

Este software esta destinado a formacion, investigacion y simulacion en entornos controlados. No debe utilizarse para intentar acceder a sistemas de terceros sin autorizacion.

---

Proyecto academico de ciberseguridad y desarrollo de software.
