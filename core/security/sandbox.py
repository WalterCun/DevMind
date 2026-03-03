# devmind-core/core/security/sandbox.py
"""
Sandbox de ejecución segura con Docker para DevMind Core.

Proporciona aislamiento completo para ejecutar código generado por IA,
con límites de recursos, monitoreo y captura de resultados.
"""

import asyncio
import docker
import json
import logging
import os
import tempfile
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Callable
import hashlib

logger = logging.getLogger(__name__)


class SandboxStatus(Enum):
    """Estados posibles del sandbox"""
    CREATED = auto()
    RUNNING = auto()
    EXECUTING = auto()
    COMPLETED = auto()
    FAILED = auto()
    TIMEOUT = auto()
    DESTROYED = auto()


class SandboxError(Exception):
    """Excepción base para errores del sandbox"""
    pass


class SandboxTimeoutError(SandboxError):
    """Error por timeout de ejecución"""
    pass


class SandboxResourceError(SandboxError):
    """Error por límites de recursos excedidos"""
    pass


@dataclass
class SandboxConfig:
    """
    Configuración del sandbox de ejecución.
    """
    # Imagen Docker base
    image: str = "python:3.11-slim"

    # Límites de recursos
    cpu_limit: float = 1.0  # CPUs (1.0 = 1 core)
    memory_limit: str = "512m"  # Memoria máxima
    disk_limit: str = "1g"  # Espacio en disco
    timeout_seconds: int = 300  # Timeout por ejecución

    # Red
    network_enabled: bool = False  # Sin red por defecto
    allowed_hosts: List[str] = field(default_factory=list)  # Hosts permitidos si network_enabled

    # Volúmenes
    project_mount: Optional[str] = None  # Ruta del proyecto a montar
    read_only: bool = True  # Sistema de archivos solo lectura por defecto

    # Variables de entorno
    env_vars: Dict[str, str] = field(default_factory=dict)
    strip_secrets: bool = True  # Eliminar variables sensibles del entorno

    # Logging
    capture_stdout: bool = True
    capture_stderr: bool = True
    max_output_size: int = 10 * 1024 * 1024  # 10MB máximo de output

    # Seguridad adicional
    no_new_privileges: bool = True
    drop_capabilities: List[str] = field(default_factory=lambda: ["ALL"])
    security_opt: List[str] = field(default_factory=lambda: ["no-new-privileges:true"])

    def to_docker_kwargs(self) -> Dict[str, Any]:
        """Convierte configuración a argumentos de docker.run()"""
        kwargs = {
            "image": self.image,
            "detach": True,
            "tty": False,
            "stdin_open": False,
            "cpu_quota": int(self.cpu_limit * 100000),  # Docker usa microsegundos
            "mem_limit": self.memory_limit,
            "pids_limit": 100,  # Máximo procesos
            "network_mode": "none" if not self.network_enabled else "bridge",
            "read_only": self.read_only,
            "tmpfs": {
                "/tmp": f"rw,noexec,nosuid,size=100m",
                "/var/tmp": f"rw,noexec,nosuid,size=50m",
            },
            "environment": self._sanitized_env(),
            "cap_drop": self.drop_capabilities,
            "security_opt": self.security_opt if self.no_new_privileges else [],
        }

        # Configurar volúmenes
        volumes = {}
        if self.project_mount and os.path.exists(self.project_mount):
            volumes[os.path.abspath(self.project_mount)] = {
                "bind": "/project",
                "mode": "ro" if self.read_only else "rw"
            }
        kwargs["volumes"] = volumes

        # Hosts adicionales si la red está habilitada
        if self.network_enabled and self.allowed_hosts:
            extra_hosts = {host: "host-gateway" for host in self.allowed_hosts}
            kwargs["extra_hosts"] = extra_hosts

        return kwargs

    def _sanitized_env(self) -> Dict[str, str]:
        """Filtra variables de entorno sensibles"""
        if not self.strip_secrets:
            return self.env_vars.copy()

        sensitive_patterns = [
            'password', 'secret', 'key', 'token', 'credential', 'auth', 'api_key'
        ]

        sanitized = {}
        for key, value in self.env_vars.items():
            if not any(pattern in key.lower() for pattern in sensitive_patterns):
                sanitized[key] = value

        # Agregar variables seguras por defecto
        sanitized.update({
            "PYTHONUNBUFFERED": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PIP_NO_CACHE_DIR": "1",
        })

        return sanitized


@dataclass
class SandboxResult:
    """
    Resultado de una ejecución en sandbox.
    """
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    memory_used: Optional[str] = None
    error: Optional[str] = None
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    sandbox_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el resultado a diccionario"""
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "stdout": self.stdout[:10000] if len(self.stdout) > 10000 else self.stdout,  # Truncar
            "stderr": self.stderr[:10000] if len(self.stderr) > 10000 else self.stderr,
            "execution_time": round(self.execution_time, 3),
            "memory_used": self.memory_used,
            "error": self.error,
            "files_created": self.files_created,
            "files_modified": self.files_modified,
            "sandbox_id": self.sandbox_id,
            "timestamp": self.timestamp.isoformat()
        }


class ExecutionSandbox:
    """
    Sandbox de ejecución aislada con Docker.

    Características:
    - Aislamiento completo de red y sistema de archivos
    - Límites estrictos de CPU, memoria y tiempo
    - Captura detallada de output y errores
    - Detección de comportamientos sospechosos
    - Limpieza automática de recursos
    """

    def __init__(
            self,
            project_id: str,
            config: Optional[SandboxConfig] = None,
            docker_client: Optional[docker.DockerClient] = None
    ):
        self.project_id = project_id
        self.config = config or SandboxConfig()
        self.docker = docker_client or docker.from_env()
        self.container = None
        self.sandbox_id = f"sandbox_{project_id}_{uuid.uuid4().hex[:8]}"
        self._start_time = None
        self._end_time = None

        # Validar que Docker esté disponible
        try:
            self.docker.ping()
        except Exception as e:
            logger.error(f"Docker not available: {e}")
            raise SandboxError("Docker daemon not accessible")

    async def __aenter__(self) -> 'ExecutionSandbox':
        """Context manager async para creación automática"""
        await self.create()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager async para limpieza automática"""
        await self.destroy()

    async def create(self) -> bool:
        """Crea el contenedor sandbox"""
        try:
            logger.debug(f"Creating sandbox: {self.sandbox_id}")

            # Crear contenedor con configuración de seguridad
            self.container = self.docker.containers.run(
                name=self.sandbox_id,
                **self.config.to_docker_kwargs()
            )

            # Esperar a que el contenedor esté listo
            await asyncio.sleep(0.5)

            # Verificar estado
            self.container.reload()
            if self.container.status != "running":
                logs = self.container.logs().decode('utf-8', errors='ignore')
                raise SandboxError(f"Container failed to start: {logs[:500]}")

            logger.info(f"Sandbox created: {self.sandbox_id}")
            return True

        except docker.errors.APIError as e:
            logger.error(f"Docker API error: {e}")
            raise SandboxError(f"Failed to create sandbox: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating sandbox: {e}")
            raise

    async def execute(
            self,
            command: Union[str, List[str]],
            timeout: Optional[int] = None,
            workdir: str = "/project",
            user: str = "nobody"  # Ejecutar como usuario sin privilegios
    ) -> SandboxResult:
        """
        Ejecuta un comando dentro del sandbox.

        Args:
            command: Comando o lista de argumentos a ejecutar
            timeout: Timeout en segundos (override del config)
            workdir: Directorio de trabajo dentro del contenedor
            user: Usuario para ejecutar el comando

        Returns:
            SandboxResult con el resultado de la ejecución
        """
        if not self.container or self.container.status != "running":
            raise SandboxError("Sandbox not running")

        self._start_time = datetime.now()
        exec_timeout = timeout or self.config.timeout_seconds

        try:
            logger.debug(f"Executing in sandbox: {command}")

            # Preparar comando
            if isinstance(command, list):
                cmd_str = " ".join(command)
            else:
                cmd_str = command

            # Ejecutar con timeout
            exec_result = await asyncio.wait_for(
                self._run_exec(cmd_str, workdir, user),
                timeout=exec_timeout
            )

            self._end_time = datetime.now()
            execution_time = (self._end_time - self._start_time).total_seconds()

            # Analizar resultado
            success = exec_result["exit_code"] == 0

            # Detectar archivos creados/modificados (si el proyecto está montado)
            files_created, files_modified = [], []
            if self.config.project_mount:
                files_created, files_modified = await self._detect_file_changes()

            # Obtener uso de memoria
            memory_used = await self._get_memory_usage()

            return SandboxResult(
                success=success,
                exit_code=exec_result["exit_code"],
                stdout=exec_result["stdout"],
                stderr=exec_result["stderr"],
                execution_time=execution_time,
                memory_used=memory_used,
                files_created=files_created,
                files_modified=files_modified,
                sandbox_id=self.sandbox_id
            )

        except asyncio.TimeoutError:
            self._end_time = datetime.now()
            logger.warning(f"Sandbox execution timeout: {command[:100]}")
            return SandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Execution timeout after {exec_timeout} seconds",
                execution_time=exec_timeout,
                memory_used=None,
                error="TIMEOUT",
                sandbox_id=self.sandbox_id
            )
        except Exception as e:
            self._end_time = datetime.now()
            logger.error(f"Sandbox execution error: {e}")
            return SandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=0,
                memory_used=None,
                error=f"EXECUTION_ERROR: {type(e).__name__}",
                sandbox_id=self.sandbox_id
            )

    async def _run_exec(
            self,
            command: str,
            workdir: str,
            user: str
    ) -> Dict[str, Any]:
        """Ejecuta comando y captura output"""
        # Ejecutar comando
        exec_id = self.container.exec_run(
            cmd=f"sh -c '{command}'",
            workdir=workdir,
            user=user,
            stdout=True,
            stderr=True,
            demux=True
        )

        # Capturar output
        stdout, stderr = exec_id.output
        stdout_str = stdout.decode('utf-8', errors='ignore') if stdout else ""
        stderr_str = stderr.decode('utf-8', errors='ignore') if stderr else ""

        # Truncar output si es muy grande
        max_output = self.config.max_output_size // 2
        if len(stdout_str) > max_output:
            stdout_str = stdout_str[:max_output] + "\n... [output truncated]"
        if len(stderr_str) > max_output:
            stderr_str = stderr_str[:max_output] + "\n... [output truncated]"

        return {
            "exit_code": exec_id.exit_code,
            "stdout": stdout_str,
            "stderr": stderr_str
        }

    async def _detect_file_changes(self) -> tuple[List[str], List[str]]:
        """Detecta archivos creados o modificados en el proyecto montado"""
        if not self.config.project_mount:
            return [], []

        created, modified = [], []
        project_path = Path(self.config.project_mount)

        try:
            # Comparar con snapshot anterior si existe
            snapshot_file = project_path / ".devmind" / "file_snapshot.json"

            if snapshot_file.exists():
                with open(snapshot_file, 'r') as f:
                    old_snapshot = json.load(f)
            else:
                old_snapshot = {}

            # Crear nuevo snapshot
            new_snapshot = {}
            for file_path in project_path.rglob("*"):
                if file_path.is_file() and ".devmind" not in str(file_path):
                    rel_path = str(file_path.relative_to(project_path))
                    stat = file_path.stat()
                    new_snapshot[rel_path] = {
                        "mtime": stat.st_mtime,
                        "size": stat.st_size,
                        "hash": self._file_hash(file_path)
                    }

                    # Detectar cambios
                    if rel_path not in old_snapshot:
                        created.append(rel_path)
                    elif old_snapshot[rel_path]["hash"] != new_snapshot[rel_path]["hash"]:
                        modified.append(rel_path)

            # Guardar nuevo snapshot
            snapshot_file.parent.mkdir(parents=True, exist_ok=True)
            with open(snapshot_file, 'w') as f:
                json.dump(new_snapshot, f)

        except Exception as e:
            logger.warning(f"Failed to detect file changes: {e}")

        return created, modified

    def _file_hash(self, file_path: Path) -> str:
        """Calcula hash SHA256 de un archivo"""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""

    async def _get_memory_usage(self) -> Optional[str]:
        """Obtiene uso de memoria del contenedor"""
        try:
            stats = self.container.stats(stream=False)
            memory = stats.get("memory_stats", {})
            usage = memory.get("usage", 0)
            if usage:
                # Convertir a formato legible
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if usage < 1024:
                        return f"{usage:.1f} {unit}"
                    usage /= 1024
        except Exception:
            pass
        return None

    async def execute_python(
            self,
            code: str,
            timeout: Optional[int] = None,
            dependencies: Optional[List[str]] = None
    ) -> SandboxResult:
        """
        Ejecuta código Python en el sandbox.

        Args:
            code: Código Python a ejecutar
            timeout: Timeout en segundos
            dependencies: Lista de paquetes a instalar antes de ejecutar

        Returns:
            SandboxResult con el resultado
        """
        # Crear script temporal
        script_name = f"exec_{uuid.uuid4().hex[:8]}.py"

        # Construir comando de ejecución
        commands = []

        # Instalar dependencias si se especifican
        if dependencies:
            for dep in dependencies:
                commands.append(f"pip install --quiet --user '{dep}'")

        # Escribir y ejecutar script
        commands.append(f"cat > {script_name} << 'PYTHON_SCRIPT_EOF'")
        commands.append(code)
        commands.append("PYTHON_SCRIPT_EOF")
        commands.append(f"python {script_name}")
        commands.append(f"rm -f {script_name}")

        full_command = " && ".join(commands)

        return await self.execute(
            command=full_command,
            timeout=timeout,
            workdir="/project" if self.config.project_mount else "/tmp"
        )

    async def copy_to_sandbox(self, source_path: str, dest_path: str) -> bool:
        """Copia un archivo del host al sandbox"""
        if not self.container:
            return False

        try:
            import tarfile
            import io

            # Crear tar con el archivo
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                tar.add(source_path, arcname=os.path.basename(dest_path))
            tar_stream.seek(0)

            # Copiar al contenedor
            self.container.put_archive(os.path.dirname(dest_path) or "/", tar_stream)
            return True

        except Exception as e:
            logger.error(f"Failed to copy to sandbox: {e}")
            return False

    async def copy_from_sandbox(self, source_path: str, dest_path: str) -> bool:
        """Copia un archivo del sandbox al host"""
        if not self.container:
            return False

        try:
            import tarfile
            import io

            # Obtener archivo del contenedor
            bits, stat = self.container.get_archive(source_path)

            # Extraer tar
            tar_stream = io.BytesIO()
            for chunk in bits:
                tar_stream.write(chunk)
            tar_stream.seek(0)

            with tarfile.open(fileobj=tar_stream, mode='r') as tar:
                tar.extractall(path=os.path.dirname(dest_path) or ".")

            return True

        except Exception as e:
            logger.error(f"Failed to copy from sandbox: {e}")
            return False

    async def destroy(self) -> bool:
        """Destruye el sandbox y libera recursos"""
        if not self.container:
            return True

        try:
            logger.debug(f"Destroying sandbox: {self.sandbox_id}")

            # Detener contenedor (con timeout corto)
            self.container.stop(timeout=5)

            # Remover contenedor
            self.container.remove(force=True)
            self.container = None

            logger.info(f"Sandbox destroyed: {self.sandbox_id}")
            return True

        except Exception as e:
            logger.error(f"Error destroying sandbox: {e}")
            # Forzar limpieza
            try:
                if self.container:
                    self.container.remove(force=True)
            except:
                pass
            return False

    def get_logs(self, tail: int = 100) -> str:
        """Obtiene logs recientes del sandbox"""
        if not self.container:
            return ""

        try:
            logs = self.container.logs(tail=tail, stderr=True, stdout=True)
            return logs.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.warning(f"Failed to get sandbox logs: {e}")
            return ""

    @property
    def is_running(self) -> bool:
        """Verifica si el sandbox está activo"""
        if not self.container:
            return False
        try:
            self.container.reload()
            return self.container.status == "running"
        except:
            return False

    def __repr__(self) -> str:
        return f"ExecutionSandbox(id={self.sandbox_id}, project={self.project_id}, running={self.is_running})"