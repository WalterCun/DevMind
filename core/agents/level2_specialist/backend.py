# devmind-core/core/agents/level2_specialist/backend.py
"""
BackendSpecialistAgent - Especialista en desarrollo backend.

Responsable de:
- Diseñar APIs REST/GraphQL
- Implementar lógica de negocio
- Gestionar bases de datos
- Asegurar seguridad y performance
"""

from typing import Dict, Any

from ..base import BaseAgent, AgentLevel, AgentStatus


class BackendSpecialistAgent(BaseAgent):
    """
    Especialista Backend - APIs, business logic, patterns.

    Nivel: SPECIALIST (2)
    Especialidad: APIs, databases, authentication, business logic
    """

    def __init__(self, **kwargs):
        """
        Inicializa el agente especialista backend.

        Args:
            **kwargs: Parámetros para BaseAgent (model, temperature, etc.)
        """
        super().__init__(
            name="Backend Specialist",
            role="Backend Specialist",
            goal="Diseñar APIs robustas, lógica de negocio escalable y arquitecturas backend seguras",
            backstory="""Eres un desarrollador Backend Senior experto en APIs REST/GraphQL,
            patrones de diseño, microservicios y bases de datos relacionales/no-relacionales.
            Priorizas seguridad, performance, escalabilidad y código mantenible.""",
            level=AgentLevel.SPECIALIST,
            **kwargs
        )

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecuta tareas de desarrollo backend"""
        self._update_status(AgentStatus.WORKING)
        context = context or {}

        try:
            task_type = self._classify_backend_task(task)

            if task_type == "api":
                result = self._create_api(task, context)
            elif task_type == "model":
                result = self._create_model(task, context)
            elif task_type == "auth":
                result = self._implement_auth(task, context)
            elif task_type == "database":
                result = self._design_database(task, context)
            else:
                result = self._general_backend_task(task, context)

            self.tasks_completed += 1
            return result

        except Exception as e:
            self.tasks_failed += 1
            return {"error": str(e), "success": False}
        finally:
            self._update_status(AgentStatus.IDLE)

    def _classify_backend_task(self, task: str) -> str:
        """Clasifica el tipo de tarea backend"""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["api", "endpoint", "rest", "graphql", "ruta"]):
            return "api"
        elif any(kw in task_lower for kw in ["modelo", "model", "entidad", "schema"]):
            return "model"
        elif any(kw in task_lower for kw in ["auth", "autenticación", "login", "jwt", "oauth"]):
            return "auth"
        elif any(kw in task_lower for kw in ["database", "tabla", "migración", "query"]):
            return "database"
        return "general"

    def _create_api(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea endpoints de API"""
        framework = context.get("framework", "Django/FastAPI")

        prompt = f"""
        Como especialista Backend, crea endpoints de API para:

        SOLICITUD: {task}

        FRAMEWORK: {framework}

        REQUISITOS:
        - Endpoints RESTful bien diseñados
        - Validación de datos de entrada
        - Manejo de errores apropiado
        - Documentación (OpenAPI/Swagger)
        - Tests básicos

        Proporciona:
        1. Código completo de endpoints
        2. Schemas de request/response
        3. Ejemplos de uso

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        api = self._parse_json_response(response.content)

        return {
            "content": api.get("content", str(api)),
            "api_code": api.get("code", ""),
            "success": True
        }

    def _create_model(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea modelos de datos"""
        orm = context.get("orm", "Django ORM/SQLAlchemy")

        prompt = f"""
        Como especialista Backend, crea modelos de datos para:

        SOLICITUD: {task}

        ORM: {orm}

        REQUISITOS:
        - Campos bien tipados
        - Relaciones definidas (FK, M2M)
        - Validaciones integradas
        - Índices apropiados
        - Migraciones

        Proporciona código completo de modelos.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        model = self._parse_json_response(response.content)

        return {
            "content": model.get("content", str(model)),
            "model_code": model.get("code", ""),
            "success": True
        }

    def _implement_auth(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Implementa autenticación/autorización"""
        auth_method = context.get("auth_method", "JWT")

        prompt = f"""
        Como especialista Backend, implementa autenticación para:

        SOLICITUD: {task}

        MÉTODO: {auth_method}

        REQUISITOS:
        - Login/registro seguros
        - Token management
        - Password hashing (bcrypt/argon2)
        - Refresh tokens
        - Protección contra ataques comunes

        Proporciona código completo con seguridad implementada.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        auth = self._parse_json_response(response.content)

        return {
            "content": auth.get("content", str(auth)),
            "auth_code": auth.get("code", ""),
            "success": True
        }

    def _design_database(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Diseña esquema de base de datos"""
        db_type = context.get("database", "PostgreSQL")

        prompt = f"""
        Como especialista Backend, diseña esquema de base de datos para:

        SOLICITUD: {task}

        DATABASE: {db_type}

        REQUISITOS:
        - Normalización apropiada
        - Índices estratégicos
        - Migraciones versionadas
        - Seed data si aplica

        Proporciona SQL/migraciones completas.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        database = self._parse_json_response(response.content)

        return {
            "content": database.get("content", str(database)),
            "database_code": database.get("code", ""),
            "success": True
        }

    def _general_backend_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Tarea backend general"""
        prompt = f"""
        Como especialista Backend, responde:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Proporciona una solución técnica completa con código si es necesario.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        result = self._parse_json_response(response.content)

        return {"content": result.get("content", str(result)), "success": True}