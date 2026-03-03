import docker
from typing import Dict, Any, Optional, List
import tempfile
import os
from pathlib import Path
import uuid


class ExecutionSandbox:
    """Sandbox seguro para ejecución de código"""

    def __init__(self, project_id: str, isolation_level: str = "strict"):
        self.project_id = project_id
        self.isolation_level = isolation_level
        self.client = docker.from_env()
        self.container = None
        self.work_dir = f"/workspace/{project_id}"

    def create(self, image: str = "python:3.11-slim") -> bool:
        """Crea el contenedor sandbox"""
        try:
            self.container = self.client.containers.run(
                image=image,
                name=f"devmind-sandbox-{self.project_id}",
                working_dir=self.work_dir,
                volumes={
                    f"./projects/{self.project_id}": {
                        'bind': self.work_dir,
                        'mode': 'rw'
                    }
                },
                network_mode="none" if self.isolation_level == "strict" else "bridge",
                cap_drop=["ALL"],
                cap_add=["CHOWN", "SETUID", "SETGID"] if self.isolation_level != "strict" else [],
                security_opt=["no-new-privileges:true"],
                read_only=True if self.isolation_level == "strict" else False,
                tmpfs={'/tmp': 'rw,noexec,nosuid,size=100m'},
                detach=True,
                tty=True
            )
            return True
        except Exception as e:
            print(f"Error creando sandbox: {e}")
            return False

    def execute(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Ejecuta comando en sandbox"""
        if not self.container:
            return {'success': False, 'error': 'Sandbox no inicializado'}

        try:
            # Ejecutar comando
            result = self.container.exec_run(
                cmd=command,
                workdir=self.work_dir,
                timeout=timeout
            )

            return {
                'success': result.exit_code == 0,
                'exit_code': result.exit_code,
                'output': result.output.decode('utf-8') if result.output else '',
                'command': command
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'command': command
            }

    def execute_python(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Ejecuta código Python en sandbox"""
        # Crear archivo temporal
        temp_file = f"temp_{uuid.uuid4().hex}.py"
        temp_path = f"{self.work_dir}/{temp_file}"

        # Escribir código (fuera del container)
        with open(f"./projects/{self.project_id}/{temp_file}", 'w') as f:
            f.write(code)

        # Ejecutar
        result = self.execute(f"python {temp_file}", timeout)

        # Limpiar
        try:
            os.remove(f"./projects/{self.project_id}/{temp_file}")
        except:
            pass

        return result

    def install_package(self, package: str) -> Dict[str, Any]:
        """Instala paquete en sandbox"""
        return self.execute(f"pip install {package}")

    def run_tests(self, test_command: str = "pytest") -> Dict[str, Any]:
        """Ejecuta tests en sandbox"""
        return self.execute(test_command)

    def get_logs(self, tail: int = 100) -> str:
        """Obtiene logs del container"""
        if not self.container:
            return ""
        return self.container.logs(tail=tail).decode('utf-8')

    def destroy(self):
        """Destruye el sandbox"""
        if self.container:
            try:
                self.container.stop()
                self.container.remove()
            except:
                pass
            self.container = None

    def __enter__(self):
        self.create()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.destroy()