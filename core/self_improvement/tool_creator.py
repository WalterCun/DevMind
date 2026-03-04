from typing import Dict, Any

from ..agents.base import BaseAgent, AgentLevel


class ToolCreatorAgent(BaseAgent):
    """Agente que crea nuevas herramientas automáticamente"""

    def __init__(self, **kwargs):
        super().__init__(
            name="Tool Builder",
            role="Creador de Herramientas Autónomo",
            goal="Crear, validar y registrar nuevas herramientas para expandir capacidades del sistema",
            backstory="""Eres un ingeniero de herramientas especializado en crear utilidades
            que resuelven problemas específicos. Tu código es modular, testeable y bien documentado.""",
            level=AgentLevel.EXECUTION,
            **kwargs
        )

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Crea una nueva herramienta"""
        self._update_status('working')

        try:
            # Analizar necesidad
            need_analysis = self._analyze_need(task, context)

            # Diseñar herramienta
            design = self._design_tool(need_analysis)

            # Implementar
            implementation = self._implement_tool(design)

            # Testear
            test_results = self._test_tool(implementation)

            if test_results['success']:
                # Registrar herramienta
                registration = self._register_tool(implementation)

                return {
                    'success': True,
                    'tool_name': design['name'],
                    'file_path': implementation['file_path'],
                    'registration': registration,
                    'test_results': test_results
                }
            else:
                return {
                    'success': False,
                    'error': 'Tool tests failed',
                    'test_results': test_results
                }

        except Exception as e:
            self.tasks_failed += 1
            return {'success': False, 'error': str(e)}
        finally:
            self._update_status('idle')

    def _analyze_need(self, task: str, context: Dict) -> Dict:
        """Analiza la necesidad de la herramienta"""
        prompt = f"""
        Analiza esta necesidad de herramienta:

        TAREA: {task}
        CONTEXTO: {context}

        Proporciona:
        1. Nombre sugerido para la herramienta
        2. Descripción de funcionalidad
        3. Inputs requeridos
        4. Outputs esperados
        5. Dependencias externas
        6. Casos de uso principales

        Responde en JSON.
        """

        response = self.llm.invoke(prompt)
        return self._parse_json_response(response.content)

    def _design_tool(self, analysis: Dict) -> Dict:
        """Diseña la arquitectura de la herramienta"""
        prompt = f"""
        Diseña la herramienta basada en este análisis:

        {analysis}

        Proporciona:
        1. Nombre de clase
        2. Métodos principales
        3. Estructura de archivos
        4. Interfaz pública
        5. Ejemplos de uso

        Responde en JSON.
        """

        response = self.llm.invoke(prompt)
        return self._parse_json_response(response.content)

    def _implement_tool(self, design: Dict) -> Dict:
        """Implementa el código de la herramienta"""
        prompt = f"""
        Implementa esta herramienta en Python:

        {design}

        Requisitos:
        1. Código limpio y documentado
        2. Type hints
        3. Manejo de errores
        4. Tests unitarios incluidos
        5. Sigue patrones de herramientas existentes

        Proporciona el código completo.
        """

        response = self.llm.invoke(prompt)

        # Guardar archivo
        file_path = f"./tools/{design['name'].lower()}.py"
        with open(file_path, 'w') as f:
            f.write(response.content)

        return {
            'code': response.content,
            'file_path': file_path
        }

    def _test_tool(self, implementation: Dict) -> Dict:
        """Testea la herramienta creada"""
        # Ejecutar tests en sandbox
        from ..security.sandbox import ExecutionSandbox

        with ExecutionSandbox(project_id="tool_test") as sandbox:
            # Copiar herramienta al sandbox
            # Ejecutar tests
            result = sandbox.execute("python -m pytest tests/ -v")

            return {
                'success': result['success'],
                'output': result.get('output', ''),
                'errors': result.get('error', '')
            }

    def _register_tool(self, implementation: Dict) -> Dict:
        """Registra la herramienta en el sistema"""
        from ..tools.registry import ToolRegistry

        registry = ToolRegistry()
        return registry.register_from_file(implementation['file_path'])

    def _parse_json_response(self, content: str) -> Dict:
        """Parsea respuesta JSON"""
        import json
        import re

        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass

        return {'raw': content}