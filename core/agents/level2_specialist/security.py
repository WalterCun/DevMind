# devmind-core/core/agents/level2_specialist/security.py
"""
SecuritySpecialistAgent - Especialista en seguridad aplicada.

Responsable de:
- Implementar autenticación/autorización segura
- Auditar vulnerabilidades
- Configurar encryption
- Asegurar compliance
"""

from typing import Dict, Any, List, Optional
from ..base import BaseAgent, AgentLevel, AgentStatus


class SecuritySpecialistAgent(BaseAgent):
    """
    Especialista Security - OWASP, auth, encryption, auditing.

    Nivel: SPECIALIST (2)
    Especialidad: Seguridad aplicada, criptografía, compliance
    """

    def __init__(self, **kwargs):
        """
        Inicializa el agente especialista en seguridad.

        Args:
            **kwargs: Parámetros para BaseAgent (model, temperature, etc.)
        """
        super().__init__(
            name="Security Specialist",
            role="Especialista en Seguridad Aplicada",
            goal="Implementar autenticación segura, proteger datos y auditar vulnerabilidades de seguridad",
            backstory="""Eres un especialista en Seguridad experto en OWASP Top 10, criptografía
            y hardening de sistemas. Tu enfoque es defensa en profundidad: múltiples capas
            de seguridad, principio de mínimo privilegio, y security by design. Priorizas
            protección de datos sensibles y prevención de ataques comunes.""",
            level=AgentLevel.SPECIALIST,
            **kwargs
        )

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecuta tareas de seguridad"""
        self._update_status(AgentStatus.WORKING)
        context = context or {}

        try:
            task_type = self._classify_security_task(task)

            if task_type == "auth":
                result = self._implement_auth(task, context)
            elif task_type == "encryption":
                result = self._implement_encryption(task, context)
            elif task_type == "audit":
                result = self._security_audit(task, context)
            elif task_type == "hardening":
                result = self._harden_system(task, context)
            else:
                result = self._general_security_task(task, context)

            self.tasks_completed += 1
            return result

        except Exception as e:
            self.tasks_failed += 1
            return {"error": str(e), "success": False}
        finally:
            self._update_status(AgentStatus.IDLE)

    def _classify_security_task(self, task: str) -> str:
        """Clasifica el tipo de tarea de seguridad"""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["auth", "login", "oauth", "jwt", "sesión"]):
            return "auth"
        elif any(kw in task_lower for kw in ["encrypt", "cifrar", "hash", "bcrypt", "crypto"]):
            return "encryption"
        elif any(kw in task_lower for kw in ["auditoría", "vulnerabilidad", "pentest", "owasp"]):
            return "audit"
        elif any(kw in task_lower for kw in ["hardening", "seguro", "proteger", "firewall"]):
            return "hardening"
        return "general"

    def _implement_auth(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Implementa autenticación/autorización"""
        auth_method = context.get("method", "JWT")

        prompt = f"""
        Como especialista en Seguridad, implementa autenticación para:

        SOLICITUD: {task}

        MÉTODO: {auth_method}

        REQUISITOS:
        - Password hashing seguro (bcrypt/argon2)
        - Token management (refresh/rotation)
        - Protección contra brute force
        - Rate limiting
        - Secure session handling

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

    def _implement_encryption(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Implementa encryption de datos"""
        encryption_type = context.get("type", "AES-256")

        prompt = f"""
        Como especialista en Seguridad, implementa encryption para:

        SOLICITUD: {task}

        TIPO: {encryption_type}

        REQUISITOS:
        - Key management seguro
        - Encryption at rest
        - Encryption in transit (TLS)
        - Key rotation strategy

        Proporciona código completo de encryption.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        encryption = self._parse_json_response(response.content)

        return {
            "content": encryption.get("content", str(encryption)),
            "encryption_code": encryption.get("code", ""),
            "success": True
        }

    def _security_audit(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza auditoría de seguridad"""
        prompt = f"""
        Como especialista en Seguridad, realiza auditoría para:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Considera OWASP Top 10:
        1. Injection
        2. Broken Authentication
        3. Sensitive Data Exposure
        4. XML External Entities
        5. Broken Access Control
        6. Security Misconfiguration
        7. XSS
        8. Insecure Deserialization
        9. Using Components with Known Vulnerabilities
        10. Insufficient Logging & Monitoring

        Proporciona reporte completo con vulnerabilidades y fixes.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        audit = self._parse_json_response(response.content)

        return {
            "content": audit.get("content", str(audit)),
            "vulnerabilities": audit.get("vulnerabilities", []),
            "recommendations": audit.get("recommendations", []),
            "success": True
        }

    def _harden_system(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza hardening de sistema"""
        prompt = f"""
        Como especialista en Seguridad, realiza hardening para:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Proporciona:
        1. Security headers
        2. Firewall rules
        3. Secure configurations
        4. Access control policies
        5. Logging y monitoring
        6. Backup y recovery

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        hardening = self._parse_json_response(response.content)

        return {
            "content": hardening.get("content", str(hardening)),
            "hardening_configs": hardening.get("configs", []),
            "success": True
        }

    def _general_security_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Tarea de seguridad general"""
        prompt = f"""
        Como especialista en Seguridad, responde:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Proporciona una solución técnica completa con código/configs si es necesario.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        result = self._parse_json_response(response.content)

        return {"content": result.get("content", str(result)), "success": True}