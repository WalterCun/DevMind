# devmind-core/core/self_improvement/language_learner.py
"""
LanguageLearner - Aprende nuevos lenguajes y frameworks.

Este agente analiza código y documentación para aprender
nuevos lenguajes de programación y frameworks.
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

from ..agents.base import BaseAgent, AgentLevel, AgentStatus
from ..memory.vector_store import VectorMemory, MemoryCategory

logger = logging.getLogger(__name__)


class LanguageLearnerAgent(BaseAgent):
    """
    Agente especializado en aprender nuevos lenguajes.

    Características:
    - Analiza documentación oficial
    - Estudia ejemplos de código
    - Crea resúmenes de sintaxis
    - Genera cheatsheets
    - Almacena conocimiento en memoria vectorial
    - Puede aprender múltiples lenguajes en paralelo
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="Language Learner",
            role="Aprendiz de Lenguajes Autónomo",
            goal="Aprender nuevos lenguajes de programación y frameworks para expandir las capacidades de codificación del equipo",
            backstory="""Eres un políglota de programación experto en aprender rápidamente
            nuevos lenguajes estudiando documentación, ejemplos y patrones comunes.
            Creas resúmenes prácticos y cheatsheets que otros agentes pueden consultar.""",
            level=AgentLevel.SPECIALIST,
            **kwargs
        )

        self.memory: Optional[VectorMemory] = None
        self.languages_learned = 0
        self.frameworks_learned = 0
        self.learning_progress: Dict[str, Dict[str, Any]] = {}

    def set_memory(self, vector_memory: VectorMemory) -> None:
        """Establece la memoria vectorial para almacenar conocimiento"""
        self.memory = vector_memory

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Aprende un nuevo lenguaje o framework.

        Flujo:
        1. Identificar lenguaje/framework objetivo
        2. Obtener recursos de aprendizaje
        3. Estudiar sintaxis y patrones
        4. Crear resúmenes y cheatsheets
        5. Almacenar en memoria vectorial

        Args:
            task: Nombre del lenguaje/framework a aprender
            context: Recursos disponibles (docs, ejemplos, etc.)

        Returns:
            Dict con resultado del aprendizaje
        """
        self._update_status(AgentStatus.WORKING)
        context = context or {}

        try:
            # Paso 1: Identificar lenguaje/framework
            identification = self._identify_language(task, context)
            lang_name = identification.get("name", "unknown")
            logger.info(f"Aprendiendo: {lang_name} ({identification.get('type')})")

            # Paso 2: Obtener recursos
            resources = self._gather_resources(identification, context)
            logger.info(f"Recursos reunidos: {len(resources)}")

            # Paso 3: Estudiar
            study_results = self._study_language(identification, resources)

            # Paso 4: Crear resúmenes
            summaries = self._create_summaries(identification, study_results)

            # Paso 5: Almacenar en memoria
            if self.memory:
                stored = self._store_knowledge(identification, summaries)
                logger.info(f"Conocimiento almacenado: {stored} entradas")

            # Actualizar progreso
            self._update_learning_progress(lang_name, identification, summaries)

            # Actualizar contador
            if identification.get("type") == "language":
                self.languages_learned += 1
            else:
                self.frameworks_learned += 1

            return {
                "success": True,
                "language": lang_name,
                "type": identification.get("type"),
                "resources_studied": len(resources),
                "summaries_created": len(summaries),
                "knowledge_stored": self.memory is not None,
                "proficiency": self._estimate_proficiency(study_results),
                "message": f"Aprendizaje de {lang_name} completado"
            }

        except Exception as e:
            logger.error(f"LanguageLearner error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            self._update_status(AgentStatus.IDLE)

    def _identify_language(
            self,
            task: str,
            context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identifica el lenguaje/framework a aprender"""
        prompt = f"""
        Identifica el lenguaje o framework a aprender:

        TAREA: {task}
        CONTEXTO: {json.dumps(context, indent=2)}

        Proporciona:
        1. name: Nombre oficial del lenguaje/framework
        2. type: "language", "framework", "library", o "tool"
        3. version: Versión más reciente estable recomendada
        4. official_site: URL del sitio web oficial
        5. documentation: URL de la documentación principal
        6. prerequisites: Lista de lenguajes/conocimientos prerrequisito
        7. use_cases: Lista de 5 casos de uso principales
        8. ecosystem: Package manager y herramientas principales

        Responde SOLO en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        return self._parse_json_response(response.content)

    def _gather_resources(
            self,
            identification: Dict[str, Any],
            context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Reúne recursos de aprendizaje"""
        resources = []

        # Recurso 1: Documentación oficial
        if identification.get("documentation"):
            resources.append({
                "type": "official_docs",
                "url": identification["documentation"],
                "priority": 1,
                "description": "Documentación oficial principal"
            })

        # Recurso 2: GitHub
        resources.append({
            "type": "github",
            "url": f"https://github.com/topics/{identification.get('name', '').lower().replace(' ', '-')}",
            "priority": 2,
            "description": "Repositorios y ejemplos en GitHub"
        })

        # Recurso 3: Ejemplos de código
        resources.append({
            "type": "code_examples",
            "description": "Ejemplos de código comunes y patrones",
            "priority": 3
        })

        # Recurso 4: Tutoriales
        resources.append({
            "type": "tutorials",
            "description": "Tutoriales paso a paso para principiantes",
            "priority": 4
        })

        # Recursos adicionales del contexto
        if "additional_resources" in context:
            for res in context["additional_resources"]:
                resources.append({**res, "priority": 5})

        return sorted(resources, key=lambda x: x.get("priority", 99))

    def _study_language(
            self,
            identification: Dict[str, Any],
            resources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Estudia el lenguaje/framework y genera resumen técnico"""
        prompt = f"""
        Estudia este lenguaje/framework y proporciona un resumen técnico completo:

        LENGUAJE: {identification.get('name')}
        TIPO: {identification.get('type')}
        VERSIÓN: {identification.get('version')}

        Proporciona un resumen estructurado con:

        1. syntax_basics:
           - Variables y tipos de datos
           - Funciones y métodos
           - Clases y estructuras (si aplica)
           - Control de flujo

        2. type_system: Descripción del sistema de tipos

        3. error_handling: Cómo se manejan errores y excepciones

        4. common_patterns: 5-10 patrones comunes del lenguaje

        5. best_practices: 5-10 mejores prácticas específicas

        6. anti_patterns: 3-5 anti-patrones a evitar

        7. ecosystem:
           - Package manager
           - Herramientas de build/test
           - IDEs recomendados

        8. learning_curve: Estimación de dificultad (beginner/intermediate/advanced)

        9. code_samples: 3 ejemplos de código completo con comentarios

        Responde SOLO en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        return self._parse_json_response(response.content)

    def _create_summaries(
            self,
            identification: Dict[str, Any],
            study_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Crea resúmenes y cheatsheets organizados por categoría"""
        summaries = []

        # Cheatsheet de sintaxis
        if "syntax_basics" in study_results:
            summaries.append({
                "title": f"{identification['name']}: Sintaxis Básica",
                "content": json.dumps(study_results["syntax_basics"], indent=2, ensure_ascii=False),
                "category": "syntax",
                "searchable": True
            })

        # Patrones comunes
        if "common_patterns" in study_results:
            summaries.append({
                "title": f"{identification['name']}: Patrones Comunes",
                "content": "\n".join([f"- {p}" for p in study_results["common_patterns"]]),
                "category": "patterns",
                "searchable": True
            })

        # Mejores prácticas
        if "best_practices" in study_results:
            summaries.append({
                "title": f"{identification['name']}: Mejores Prácticas",
                "content": "\n".join([f"- {p}" for p in study_results["best_practices"]]),
                "category": "best_practices",
                "searchable": True
            })

        # Ejemplos de código
        if "code_samples" in study_results:
            for i, sample in enumerate(study_results["code_samples"]):
                summaries.append({
                    "title": f"{identification['name']}: Ejemplo {i + 1}",
                    "content": sample,
                    "category": "examples",
                    "searchable": False  # Código completo, mejor buscar por metadata
                })

        # Anti-patrones
        if "anti_patterns" in study_results:
            summaries.append({
                "title": f"{identification['name']}: Anti-patrones a Evitar",
                "content": "\n".join([f"- ❌ {p}" for p in study_results["anti_patterns"]]),
                "category": "warnings",
                "searchable": True
            })

        return summaries

    def _store_knowledge(
            self,
            identification: Dict[str, Any],
            summaries: List[Dict[str, Any]]
    ) -> int:
        """Almacena el conocimiento en memoria vectorial"""
        if not self.memory:
            return 0

        stored = 0
        lang_name = identification.get("name", "unknown")

        for summary in summaries:
            try:
                self.memory.store(
                    content=summary["content"],
                    metadata={
                        "language": lang_name,
                        "type": identification.get("type"),
                        "category": summary["category"],
                        "title": summary["title"],
                        "searchable": summary.get("searchable", True),
                        "learned_at": datetime.now().isoformat()
                    },
                    category=MemoryCategory.DOCUMENTATION
                )
                stored += 1
            except Exception as e:
                logger.warning(f"Failed to store summary '{summary['title']}': {e}")

        logger.info(f"Stored {stored} knowledge entries for {lang_name}")
        return stored

    def _update_learning_progress(
            self,
            lang_name: str,
            identification: Dict[str, Any],
            summaries: List[Dict[str, Any]]
    ) -> None:
        """Actualiza el progreso de aprendizaje interno"""
        self.learning_progress[lang_name] = {
            "identified_at": datetime.now().isoformat(),
            "type": identification.get("type"),
            "version": identification.get("version"),
            "summaries_count": len(summaries),
            "categories": list(set(s["category"] for s in summaries)),
            "last_updated": datetime.now().isoformat()
        }

    def _estimate_proficiency(self, study_results: Dict[str, Any]) -> str:
        """Estima el nivel de proficiencia basado en el estudio"""
        # Métricas simples de proficiencia
        sections_completed = sum(1 for k in [
            "syntax_basics", "type_system", "error_handling",
            "common_patterns", "best_practices"
        ] if k in study_results)

        if sections_completed >= 5:
            return "intermediate"
        elif sections_completed >= 3:
            return "beginner"
        else:
            return "basic"

    def get_learned_languages(self) -> List[str]:
        """Obtiene lista de lenguajes aprendidos"""
        return list(self.learning_progress.keys())

    def can_code_in(self, language: str) -> bool:
        """Verifica si el agente puede codificar en un lenguaje"""
        learned = self.get_learned_languages()
        return any(
            lang.lower() == language.lower() or language.lower() in lang.lower()
            for lang in learned
        )

    def get_proficiency(self, language: str) -> Optional[Dict[str, Any]]:
        """Obtiene nivel de proficiencia en un lenguaje"""
        progress = self.learning_progress.get(language)
        if not progress:
            # Buscar por nombre parcial
            for lang, prog in self.learning_progress.items():
                if language.lower() in lang.lower():
                    return prog
        return progress

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parsea respuesta JSON del LLM de forma robusta"""
        patterns = [
            r'\{.*\}',
            r'```json\s*(.*?)\s*```',
            r'```.*?\n(.*?)\n```',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1) if len(match.groups()) > 0 else match.group())
                except json.JSONDecodeError:
                    continue

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        return {"raw": content}

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del LanguageLearner"""
        return {
            "languages_learned": self.languages_learned,
            "frameworks_learned": self.frameworks_learned,
            "total_progress_entries": len(self.learning_progress),
            "memory_available": self.memory is not None,
            "languages": list(self.learning_progress.keys())
        }
