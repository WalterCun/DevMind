# devmind-core/core/agents/level2_specialist/frontend.py
"""
FrontendSpecialistAgent - Especialista en desarrollo frontend.

Responsable de:
- Crear interfaces de usuario modernas
- Implementar componentes React/Vue/Angular
- Optimizar rendimiento frontend
- Asegurar accesibilidad y UX
"""

from typing import Dict, Any

from ..base import BaseAgent, AgentLevel, AgentStatus


class FrontendSpecialistAgent(BaseAgent):
    """
    Especialista Frontend - React, Vue, Angular, CSS, UX.

    Nivel: SPECIALIST (2)
    Especialidad: Interfaces, componentes, styling, UX, performance
    """

    def __init__(self, **kwargs):
        """
        Inicializa el agente especialista frontend.

        Args:
            **kwargs: Parámetros para BaseAgent (model, temperature, etc.)
        """
        super().__init__(
            name="Frontend Specialist",
            role="Frontend Specialist",
            goal="Crear interfaces de usuario modernas, responsivas, accesibles y de alto rendimiento",
            backstory="""Eres un desarrollador Frontend Senior con expertise en React, Vue y Angular.
            Tu pasión es crear experiencias de usuario excepcionales. Priorizas componentes
            reutilizables, código limpio, accesibilidad (WCAG), y optimización de performance.
            Conoces las últimas tendencias pero eliges pragmatismo sobre hype.""",
            level=AgentLevel.SPECIALIST,
            **kwargs
        )

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecuta tareas de desarrollo frontend.

        Args:
            task: Descripción de la tarea frontend
            context: Contexto adicional (framework, requisitos, etc.)

        Returns:
            Dict con código, componentes y recomendaciones
        """
        self._update_status(AgentStatus.WORKING)
        context = context or {}

        try:
            task_type = self._classify_frontend_task(task)

            if task_type == "component":
                result = self._create_component(task, context)
            elif task_type == "page":
                result = self._create_page(task, context)
            elif task_type == "styling":
                result = self._create_styling(task, context)
            elif task_type == "optimization":
                result = self._optimize_frontend(task, context)
            else:
                result = self._general_frontend_task(task, context)

            self.tasks_completed += 1
            return result

        except Exception as e:
            self.tasks_failed += 1
            return {"error": str(e), "success": False}
        finally:
            self._update_status(AgentStatus.IDLE)

    def _classify_frontend_task(self, task: str) -> str:
        """Clasifica el tipo de tarea frontend"""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["componente", "component", "react", "vue", "angular"]):
            return "component"
        elif any(kw in task_lower for kw in ["página", "page", "ruta", "route", "view"]):
            return "page"
        elif any(kw in task_lower for kw in ["estilo", "css", "tailwind", "scss", "diseño"]):
            return "styling"
        elif any(kw in task_lower for kw in ["optimizar", "performance", "lighthouse", "carga"]):
            return "optimization"
        return "general"

    def _create_component(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea componente frontend"""
        framework = context.get("framework", "React")

        prompt = f"""
        Como especialista Frontend, crea un componente para:

        SOLICITUD: {task}

        FRAMEWORK: {framework}

        REQUISITOS:
        - Componente funcional y reutilizable
        - Props bien tipadas (TypeScript si es posible)
        - Manejo de estados adecuado
        - Estilos modulares (CSS Modules, Tailwind, o styled-components)
        - Accesibilidad (ARIA labels, keyboard navigation)
        - Tests básicos incluidos

        Proporciona:
        1. Código completo del componente
        2. Ejemplo de uso
        3. Props/interfaces definidas
        4. Notas de implementación

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        component = self._parse_json_response(response.content)

        return {
            "content": component.get("content", str(component)),
            "component_code": component.get("code", ""),
            "framework": framework,
            "success": True
        }

    def _create_page(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea página/vista completa"""
        framework = context.get("framework", "React")
        router = context.get("router", "React Router")

        prompt = f"""
        Como especialista Frontend, crea una página completa para:

        SOLICITUD: {task}

        STACK: {framework} + {router}

        REQUISITOS:
        - Layout responsivo
        - Navegación integrada
        - Fetch de datos (si aplica)
        - Manejo de loading y errores
        - SEO básico (meta tags, headings)

        Proporciona código completo con todos los componentes necesarios.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        page = self._parse_json_response(response.content)

        return {
            "content": page.get("content", str(page)),
            "page_code": page.get("code", ""),
            "success": True
        }

    def _create_styling(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea estilos/CSS"""
        styling_tool = context.get("styling", "Tailwind CSS")

        prompt = f"""
        Como especialista Frontend, crea estilos para:

        SOLICITUD: {task}

        HERRAMIENTA: {styling_tool}

        REQUISITOS:
        - Diseño responsivo (mobile-first)
        - Variables de diseño consistentes
        - Accesibilidad de colores (contraste)
        - Clases utilitarias o CSS modular

        Proporciona código de estilos completo.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        styling = self._parse_json_response(response.content)

        return {
            "content": styling.get("content", str(styling)),
            "styling_code": styling.get("code", ""),
            "success": True
        }

    def _optimize_frontend(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimiza rendimiento frontend"""
        prompt = f"""
        Como especialista Frontend, optimiza el rendimiento para:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Proporciona recomendaciones de optimización con:
        1. Code splitting
        2. Lazy loading
        3. Optimización de imágenes
        4. Caching strategies
        5. Bundle size reduction
        6. Core Web Vitals improvements

        Responde en formato JSON válido con código de ejemplo.
        """

        response = self.llm.invoke(prompt)
        optimization = self._parse_json_response(response.content)

        return {
            "content": optimization.get("content", str(optimization)),
            "optimizations": optimization.get("recommendations", []),
            "success": True
        }

    def _general_frontend_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Tarea frontend general"""
        prompt = f"""
        Como especialista Frontend, responde:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Proporciona una solución técnica completa con código si es necesario.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        result = self._parse_json_response(response.content)

        return {
            "content": result.get("content", str(result)),
            "success": True
        }