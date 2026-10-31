import os
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


class TestRedBlueTeamAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.token = "token-simulado-para-pruebas"
        self.target = "192.168.56.101"
        self.credentials = [
            {
                "username": f"lab_user_{i}",
                "password": "password-ficticio",
            }
            for i in range(10)
        ]

    def test_health(self):
        response = self.client.get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "running")

    def test_requires_token(self):
        with patch.dict(os.environ, {"LAB_API_TOKEN": self.token}):
            response = self.client.post(
                "/api/v1/red-team/ssh-scenario",
                json={"ip": self.target},
            )

        self.assertEqual(response.status_code, 401)

    def test_rejects_invalid_token(self):
        with patch.dict(os.environ, {"LAB_API_TOKEN": self.token}):
            response = self.client.post(
                "/api/v1/red-team/ssh-scenario",
                json={"ip": self.target},
                headers={"X-Lab-Token": "token-incorrecto"},
            )

        self.assertEqual(response.status_code, 401)

    def test_rejects_unauthorized_target(self):
        with (
            patch.dict(os.environ, {"LAB_API_TOKEN": self.token}),
            patch(
                "main.cargar_configuracion",
                return_value=(
                    self.target,
                    self.credentials,
                    Path("known_hosts_simulado"),
                ),
            ),
            patch("main.intentar_ssh") as mock_ssh,
        ):
            response = self.client.post(
                "/api/v1/red-team/ssh-scenario",
                json={"ip": "192.168.56.200"},
                headers={"X-Lab-Token": self.token},
            )

        self.assertEqual(response.status_code, 403)
        mock_ssh.assert_not_called()

    def test_invalid_ip(self):
        with patch.dict(os.environ, {"LAB_API_TOKEN": self.token}):
            response = self.client.post(
                "/api/v1/red-team/ssh-scenario",
                json={"ip": "direccion-invalida"},
                headers={"X-Lab-Token": self.token},
            )

        self.assertEqual(response.status_code, 422)

    def test_ten_simulated_attempts(self):
        with (
            patch.dict(os.environ, {"LAB_API_TOKEN": self.token}),
            patch(
                "main.cargar_configuracion",
                return_value=(
                    self.target,
                    self.credentials,
                    Path("known_hosts_simulado"),
                ),
            ),
            patch(
                "main.intentar_ssh",
                return_value="FAILED",
            ) as mock_ssh,
            patch("main.time.sleep") as mock_sleep,
        ):
            response = self.client.post(
                "/api/v1/red-team/ssh-scenario",
                json={"ip": self.target},
                headers={"X-Lab-Token": self.token},
            )

        self.assertEqual(response.status_code, 200)

        result = response.json()

        self.assertEqual(result["total_attempts"], 10)
        self.assertEqual(result["failed"], 10)
        self.assertEqual(result["successful"], 0)
        self.assertEqual(result["errors"], 0)
        self.assertEqual(len(result["attempts"]), 10)

        self.assertEqual(mock_ssh.call_count, 10)
        self.assertEqual(mock_sleep.call_count, 9)


if __name__ == "__main__":
    unittest.main()
