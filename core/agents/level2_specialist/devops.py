# devmind-core/core/agents/level2_specialist/devops.py
"""
DevOpsSpecialistAgent - Especialista en DevOps e infraestructura.

Responsable de:
- Configurar CI/CD pipelines
- Gestionar contenedores Docker/Kubernetes
- Automatizar despliegues
- Monitorear infraestructura
"""

from typing import Dict, Any

from ..base import BaseAgent, AgentLevel, AgentStatus


class DevOpsSpecialistAgent(BaseAgent):
    """
    Especialista DevOps - CI/CD, Docker, Kubernetes, monitoring.

    Nivel: SPECIALIST (2)
    Especialidad: Infraestructura, automatización, cloud, monitoring
    """

    def __init__(self, **kwargs):
        """
        Inicializa el agente especialista DevOps.

        Args:
            **kwargs: Parámetros para BaseAgent (model, temperature, etc.)
        """
        super().__init__(
            name="DevOps Specialist",
            role="Especialista en DevOps e Infraestructura",
            goal="Automatizar despliegues, configurar infraestructura como código y asegurar observabilidad del sistema",
            backstory="""Eres un ingeniero DevOps/SRE experto en Docker, Kubernetes, CI/CD
            y cloud (AWS/GCP/Azure). Tu filosofía es automatización total: todo como código,
            despliegues frecuentes y seguros, monitoring proactivo. Priorizas seguridad,
            resiliencia y eficiencia de costos.""",
            level=AgentLevel.SPECIALIST,
            **kwargs
        )

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecuta tareas de DevOps"""
        self._update_status(AgentStatus.WORKING)
        context = context or {}

        try:
            task_type = self._classify_devops_task(task)

            if task_type == "docker":
                result = self._create_docker_config(task, context)
            elif task_type == "cicd":
                result = self._create_cicd_pipeline(task, context)
            elif task_type == "kubernetes":
                result = self._create_k8s_config(task, context)
            elif task_type == "cloud":
                result = self._configure_cloud(task, context)
            elif task_type == "monitoring":
                result = self._setup_monitoring(task, context)
            else:
                result = self._general_devops_task(task, context)

            self.tasks_completed += 1
            return result

        except Exception as e:
            self.tasks_failed += 1
            return {"error": str(e), "success": False}
        finally:
            self._update_status(AgentStatus.IDLE)

    def _classify_devops_task(self, task: str) -> str:
        """Clasifica el tipo de tarea DevOps"""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["docker", "contenedor", "image", "dockerfile"]):
            return "docker"
        elif any(kw in task_lower for kw in ["ci/cd", "pipeline", "github actions", "gitlab", "jenkins"]):
            return "cicd"
        elif any(kw in task_lower for kw in ["kubernetes", "k8s", "helm", "deploy"]):
            return "kubernetes"
        elif any(kw in task_lower for kw in ["aws", "gcp", "azure", "cloud", "terraform"]):
            return "cloud"
        elif any(kw in task_lower for kw in ["monitoring", "prometheus", "grafana", "logs"]):
            return "monitoring"
        return "general"

    def _create_docker_config(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea configuración Docker"""
        prompt = f"""
        Como especialista DevOps, crea configuración Docker para:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Proporciona:
        1. Dockerfile optimizado (multi-stage si aplica)
        2. docker-compose.yml si es necesario
        3. .dockerignore
        4. Best practices de seguridad
        5. Comandos de build/run

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        docker_config = self._parse_json_response(response.content)

        return {
            "content": docker_config.get("content", str(docker_config)),
            "dockerfile": docker_config.get("dockerfile", ""),
            "docker_compose": docker_config.get("compose", ""),
            "success": True
        }

    def _create_cicd_pipeline(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea pipeline de CI/CD"""
        platform = context.get("platform", "GitHub Actions")

        prompt = f"""
        Como especialista DevOps, crea pipeline de CI/CD para:

        SOLICITUD: {task}

        PLATAFORMA: {platform}

        REQUISITOS:
        - Build automático
        - Tests automáticos
        - Linting/validación de código
        - Deploy a staging/production
        - Notificaciones

        Proporciona configuración completa del pipeline.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        pipeline = self._parse_json_response(response.content)

        return {
            "content": pipeline.get("content", str(pipeline)),
            "pipeline_config": pipeline.get("config", ""),
            "success": True
        }

    def _create_k8s_config(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea configuración Kubernetes"""
        prompt = f"""
        Como especialista DevOps, crea configuración Kubernetes para:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Proporciona:
        1. Deployments
        2. Services
        3. ConfigMaps/Secrets
        4. Ingress
        5. HPA (Horizontal Pod Autoscaler)
        6. Helm chart si aplica

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        k8s_config = self._parse_json_response(response.content)

        return {
            "content": k8s_config.get("content", str(k8s_config)),
            "k8s_manifests": k8s_config.get("manifests", ""),
            "success": True
        }

    def _configure_cloud(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Configura infraestructura cloud"""
        provider = context.get("provider", "AWS")

        prompt = f"""
        Como especialista DevOps, configura infraestructura cloud para:

        SOLICITUD: {task}

        PROVIDER: {provider}

        Proporciona:
        1. Arquitectura recomendada
        2. Terraform/CloudFormation scripts
        3. IAM roles/policies
        4. VPC/Networking config
        5. Cost optimization tips

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        cloud_config = self._parse_json_response(response.content)

        return {
            "content": cloud_config.get("content", str(cloud_config)),
            "infrastructure_code": cloud_config.get("code", ""),
            "success": True
        }

    def _setup_monitoring(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Configura monitoring y observabilidad"""
        prompt = f"""
        Como especialista DevOps, configura monitoring para:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Proporciona:
        1. Métricas clave a monitorear
        2. Config de Prometheus/Grafana
        3. Alertas recomendadas
        4. Logging strategy (ELK, Loki, etc.)
        5. Distributed tracing si aplica

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        monitoring = self._parse_json_response(response.content)

        return {
            "content": monitoring.get("content", str(monitoring)),
            "monitoring_config": monitoring.get("config", ""),
            "alerts": monitoring.get("alerts", []),
            "success": True
        }

    def _general_devops_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Tarea DevOps general"""
        prompt = f"""
        Como especialista DevOps, responde:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Proporciona una solución técnica completa con configs/scripts si es necesario.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        result = self._parse_json_response(response.content)

        return {"content": result.get("content", str(result)), "success": True}