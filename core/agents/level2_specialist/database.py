# devmind-core/core/agents/level2_specialist/database.py
"""
DatabaseSpecialistAgent - Especialista en bases de datos.

Responsable de:
- Diseñar esquemas de bases de datos
- Optimizar queries y rendimiento
- Gestionar migraciones
- Asegurar integridad de datos
"""

from typing import Dict, Any

from ..base import BaseAgent, AgentLevel, AgentStatus


class DatabaseSpecialistAgent(BaseAgent):
    """
    Especialista Database - SQL, NoSQL, migrations, optimización.

    Nivel: SPECIALIST (2)
    Especialidad: Bases de datos relacionales, NoSQL, optimización
    """

    def __init__(self, **kwargs):
        """
        Inicializa el agente especialista en bases de datos.

        Args:
            **kwargs: Parámetros para BaseAgent (model, temperature, etc.)
        """
        super().__init__(
            name="Database Specialist",
            role="Especialista en Bases de Datos",
            goal="Diseñar esquemas eficientes, optimizar queries y gestionar migraciones de bases de datos",
            backstory="""Eres un DBA/Ingeniero de Datos experto en PostgreSQL, MySQL, MongoDB
            y optimización de bases de datos. Tu enfoque es pragmático: priorizas integridad,
            performance y escalabilidad de datos. Conoces patrones de diseño de esquemas
            y mejores prácticas de la industria.""",
            level=AgentLevel.SPECIALIST,
            **kwargs
        )

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecuta tareas de bases de datos.

        Args:
            task: Descripción de la tarea de database
            context: Contexto adicional (DB type, requisitos, etc.)

        Returns:
            Dict con código SQL, esquemas y recomendaciones
        """
        self._update_status(AgentStatus.WORKING)
        context = context or {}

        try:
            task_type = self._classify_database_task(task)

            if task_type == "schema":
                result = self._design_schema(task, context)
            elif task_type == "query":
                result = self._optimize_query(task, context)
            elif task_type == "migration":
                result = self._create_migration(task, context)
            elif task_type == "optimization":
                result = self._optimize_database(task, context)
            else:
                result = self._general_database_task(task, context)

            self.tasks_completed += 1
            return result

        except Exception as e:
            self.tasks_failed += 1
            return {"error": str(e), "success": False}
        finally:
            self._update_status(AgentStatus.IDLE)

    def _classify_database_task(self, task: str) -> str:
        """Clasifica el tipo de tarea de database"""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["esquema", "schema", "tabla", "modelo"]):
            return "schema"
        elif any(kw in task_lower for kw in ["query", "consulta", "select", "join"]):
            return "query"
        elif any(kw in task_lower for kw in ["migración", "migration", "alter", "migrate"]):
            return "migration"
        elif any(kw in task_lower for kw in ["optimizar", "índice", "performance", "lento"]):
            return "optimization"
        return "general"

    def _design_schema(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Diseña esquema de base de datos"""
        db_type = context.get("database", "PostgreSQL")

        prompt = f"""
        Como especialista en Bases de Datos, diseña un esquema para:

        SOLICITUD: {task}

        DATABASE: {db_type}

        REQUISITOS:
        - Normalización apropiada (3NF o según necesite)
        - Claves primarias y foráneas definidas
        - Índices estratégicos
        - Tipos de datos apropiados
        - Constraints de integridad

        Proporciona:
        1. Diagrama ER en formato texto
        2. SQL de creación de tablas
        3. Índices recomendados
        4. Justificación de decisiones de diseño

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        schema = self._parse_json_response(response.content)

        return {
            "content": schema.get("content", str(schema)),
            "schema_sql": schema.get("sql", ""),
            "success": True
        }

    def _optimize_query(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimiza queries de base de datos"""
        query = context.get("query", "")

        prompt = f"""
        Como especialista en Bases de Datos, optimiza esta query:

        SOLICITUD: {task}

        QUERY ORIGINAL:
        {query if query else "No proporcionada"}

        Proporciona:
        1. Análisis de la query actual
        2. Query optimizada
        3. Índices recomendados
        4. Explicación del plan de ejecución
        5. Mejoras de performance esperadas

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        optimization = self._parse_json_response(response.content)

        return {
            "content": optimization.get("content", str(optimization)),
            "optimized_query": optimization.get("query", ""),
            "success": True
        }

    def _create_migration(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea migraciones de base de datos"""
        framework = context.get("framework", "Django/SQLAlchemy")

        prompt = f"""
        Como especialista en Bases de Datos, crea una migración para:

        SOLICITUD: {task}

        FRAMEWORK: {framework}

        REQUISITOS:
        - Migración reversible (up/down)
        - Preservación de datos existentes
        - Testing de la migración
        - Rollback plan

        Proporciona código completo de migración.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        migration = self._parse_json_response(response.content)

        return {
            "content": migration.get("content", str(migration)),
            "migration_code": migration.get("code", ""),
            "success": True
        }

    def _optimize_database(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimiza rendimiento de base de datos"""
        prompt = f"""
        Como especialista en Bases de Datos, optimiza el rendimiento para:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Proporciona recomendaciones de optimización con:
        1. Índices a crear/eliminar
        2. Configuración de database (shared_buffers, etc.)
        3. Query optimization strategies
        4. Connection pooling
        5. Partitioning si aplica
        6. Monitoring recommendations

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        optimization = self._parse_json_response(response.content)

        return {
            "content": optimization.get("content", str(optimization)),
            "optimizations": optimization.get("recommendations", []),
            "success": True
        }

    def _general_database_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Tarea de database general"""
        prompt = f"""
        Como especialista en Bases de Datos, responde:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Proporciona una solución técnica completa con código SQL si es necesario.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        result = self._parse_json_response(response.content)

        return {"content": result.get("content", str(result)), "success": True}