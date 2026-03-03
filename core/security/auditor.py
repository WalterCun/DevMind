# devmind-core/core/security/auditor.py
"""
Sistema de auditoría para DevMind Core.

Registra y audita todas las acciones del agente para:
- Trazabilidad completa
- Detección de comportamientos anómalos
- Cumplimiento de políticas
- Forense post-ejecución
"""

import json
import logging
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


class AuditLevel(Enum):
    """Niveles de detalle de auditoría"""
    MINIMAL = auto()  # Solo acciones críticas
    STANDARD = auto()  # Acciones normales + críticas
    VERBOSE = auto()  # Todas las acciones
    DEBUG = auto()  # Todo + detalles internos


class AuditCategory(Enum):
    """Categorías de eventos auditables"""
    FILE_OPERATION = auto()
    CODE_EXECUTION = auto()
    NETWORK_ACTIVITY = auto()
    DATABASE_OPERATION = auto()
    AGENT_ACTION = auto()
    SECURITY_EVENT = auto()
    CONFIGURATION_CHANGE = auto()
    ERROR = auto()


class AuditStatus(Enum):
    """Estado de un evento auditado"""
    ALLOWED = auto()
    BLOCKED = auto()
    CONFIRMED = auto()
    PENDING = auto()
    FLAGGED = auto()


@dataclass
class AuditEntry:
    """
    Entrada individual en el log de auditoría.
    """
    timestamp: datetime
    event_id: str
    category: AuditCategory
    action: str
    status: AuditStatus
    agent_name: str
    project_id: str
    session_id: str
    details: Dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0
    confirmation_by: Optional[str] = None
    execution_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_id": self.event_id,
            "category": self.category.name,
            "action": self.action,
            "status": self.status.name,
            "agent_name": self.agent_name,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "details": self.details,
            "risk_score": self.risk_score,
            "confirmation_by": self.confirmation_by,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class AuditSummary:
    """
    Resumen de auditoría para un período.
    """
    period_start: datetime
    period_end: datetime
    total_events: int
    by_category: Dict[str, int]
    by_status: Dict[str, int]
    by_agent: Dict[str, int]
    high_risk_events: List[AuditEntry]
    blocked_events: List[AuditEntry]
    avg_risk_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_events": self.total_events,
            "by_category": self.by_category,
            "by_status": self.by_status,
            "by_agent": self.by_agent,
            "high_risk_events_count": len(self.high_risk_events),
            "blocked_events_count": len(self.blocked_events),
            "avg_risk_score": round(self.avg_risk_score, 3)
        }


class SecurityAuditor:
    """
    Auditor principal de seguridad para DevMind Core.

    Características:
    - Logging estructurado de todas las acciones
    - Detección de anomalías en tiempo real
    - Alertas configurables por riesgo
    - Exportación de reportes
    - Retención configurable de logs
    """

    def __init__(
            self,
            project_id: str,
            log_dir: Optional[str] = None,
            audit_level: AuditLevel = AuditLevel.STANDARD,
            retention_days: int = 30,
            alert_threshold: float = 0.8
    ):
        self.project_id = project_id
        self.log_dir = Path(log_dir) if log_dir else Path.home() / ".devmind" / "audits" / project_id
        self.audit_level = audit_level
        self.retention_days = retention_days
        self.alert_threshold = alert_threshold

        # Almacenamiento en memoria para acceso rápido
        self._entries: List[AuditEntry] = []
        self._entries_lock = threading.Lock()

        # Contadores en tiempo real
        self._counters = defaultdict(int)
        self._risk_accumulator = 0.0

        # Callbacks para alertas
        self._alert_callbacks: List[Callable[[AuditEntry], None]] = []

        # Configurar log file
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = self._get_today_log_file()

        logger.info(f"SecurityAuditor initialized for project {project_id}")

    def _get_today_log_file(self) -> Path:
        """Obtiene el archivo de log del día actual"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"audit_{today}.jsonl"

    def _generate_event_id(self) -> str:
        """Genera ID único para evento"""
        timestamp = datetime.now().isoformat()
        random = hashlib.md5(f"{timestamp}{threading.current_thread().ident}".encode()).hexdigest()[:8]
        return f"evt_{random}"

    def log(
            self,
            category: AuditCategory,
            action: str,
            status: AuditStatus,
            agent_name: str,
            session_id: str,
            details: Optional[Dict[str, Any]] = None,
            risk_score: float = 0.0,
            confirmation_by: Optional[str] = None,
            execution_time_ms: Optional[float] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEntry:
        """
        Registra un evento de auditoría.

        Args:
            category: Categoría del evento
            action: Acción realizada
            status: Estado de la acción
            agent_name: Nombre del agente que realizó la acción
            session_id: ID de sesión actual
            details: Detalles específicos de la acción
            risk_score: Puntuación de riesgo (0-1)
            confirmation_by: Usuario que confirmó (si aplica)
            execution_time_ms: Tiempo de ejecución en ms
            metadata: Metadata adicional

        Returns:
            AuditEntry creada
        """
        # Verificar nivel de auditoría
        if not self._should_log(category, status, risk_score):
            return None

        entry = AuditEntry(
            timestamp=datetime.now(),
            event_id=self._generate_event_id(),
            category=category,
            action=action,
            status=status,
            agent_name=agent_name,
            project_id=self.project_id,
            session_id=session_id,
            details=details or {},
            risk_score=risk_score,
            confirmation_by=confirmation_by,
            execution_time_ms=execution_time_ms,
            metadata=metadata or {}
        )

        # Guardar en memoria
        with self._entries_lock:
            self._entries.append(entry)
            self._counters[category.name] += 1
            self._counters[status.name] += 1
            self._counters[agent_name] += 1
            self._risk_accumulator += risk_score

        # Guardar en archivo
        self._write_to_file(entry)

        # Verificar alertas
        if risk_score >= self.alert_threshold:
            self._trigger_alerts(entry)

        # Limpiar logs antiguos
        self._cleanup_old_logs()

        return entry

    def _should_log(
            self,
            category: AuditCategory,
            status: AuditStatus,
            risk_score: float
    ) -> bool:
        """Determina si un evento debe ser logueado según el nivel"""
        if self.audit_level == AuditLevel.DEBUG:
            return True

        if self.audit_level == AuditLevel.VERBOSE:
            return True

        if self.audit_level == AuditLevel.STANDARD:
            # Loguear todo excepto operaciones de archivo simples
            if category == AuditCategory.FILE_OPERATION and status == AuditStatus.ALLOWED:
                return risk_score > 0.3
            return True

        if self.audit_level == AuditLevel.MINIMAL:
            # Solo eventos críticos
            return (
                    status in [AuditStatus.BLOCKED, AuditStatus.FLAGGED] or
                    risk_score >= 0.7 or
                    category == AuditCategory.SECURITY_EVENT
            )

        return True

    def _write_to_file(self, entry: AuditEntry) -> None:
        """Escribe entrada en archivo JSONL"""
        try:
            # Rotar archivo si es nuevo día
            today_file = self._get_today_log_file()
            if today_file != self._log_file:
                self._log_file = today_file

            with open(self._log_file, 'a', encoding='utf-8') as f:
                f.write(entry.to_json() + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit entry: {e}")

    def _trigger_alerts(self, entry: AuditEntry) -> None:
        """Ejecuta callbacks de alerta para eventos de alto riesgo"""
        for callback in self._alert_callbacks:
            try:
                callback(entry)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

    def _cleanup_old_logs(self) -> None:
        """Elimina logs más antiguos que retention_days"""
        try:
            cutoff = datetime.now() - timedelta(days=self.retention_days)

            for log_file in self.log_dir.glob("audit_*.jsonl"):
                # Extraer fecha del nombre del archivo
                try:
                    date_str = log_file.stem.replace("audit_", "")
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")

                    if file_date < cutoff:
                        log_file.unlink()
                        logger.debug(f"Deleted old audit log: {log_file}")
                except ValueError:
                    continue
        except Exception as e:
            logger.warning(f"Failed to cleanup old logs: {e}")

    def register_alert_callback(self, callback: Callable[[AuditEntry], None]) -> None:
        """Registra callback para alertas de alto riesgo"""
        self._alert_callbacks.append(callback)

    def get_entries(
            self,
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None,
            category: Optional[AuditCategory] = None,
            status: Optional[AuditStatus] = None,
            agent_name: Optional[str] = None,
            min_risk_score: Optional[float] = None,
            limit: int = 1000
    ) -> List[AuditEntry]:
        """
        Consulta entradas de auditoría con filtros.

        Returns:
            Lista de AuditEntry que coinciden con los filtros
        """
        with self._entries_lock:
            entries = self._entries.copy()

        # Aplicar filtros
        if start_time:
            entries = [e for e in entries if e.timestamp >= start_time]
        if end_time:
            entries = [e for e in entries if e.timestamp <= end_time]
        if category:
            entries = [e for e in entries if e.category == category]
        if status:
            entries = [e for e in entries if e.status == status]
        if agent_name:
            entries = [e for e in entries if e.agent_name == agent_name]
        if min_risk_score is not None:
            entries = [e for e in entries if e.risk_score >= min_risk_score]

        # Ordenar por timestamp descendente
        entries.sort(key=lambda e: e.timestamp, reverse=True)

        return entries[:limit]

    def get_summary(
            self,
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None
    ) -> AuditSummary:
        """
        Genera resumen de auditoría para un período.
        """
        entries = self.get_entries(start_time=start_time, end_time=end_time, limit=10000)

        if not entries:
            return AuditSummary(
                period_start=start_time or datetime.now(),
                period_end=end_time or datetime.now(),
                total_events=0,
                by_category={},
                by_status={},
                by_agent={},
                high_risk_events=[],
                blocked_events=[],
                avg_risk_score=0.0
            )

        # Calcular estadísticas
        by_category = defaultdict(int)
        by_status = defaultdict(int)
        by_agent = defaultdict(int)
        high_risk = []
        blocked = []
        risk_sum = 0.0

        for entry in entries:
            by_category[entry.category.name] += 1
            by_status[entry.status.name] += 1
            by_agent[entry.agent_name] += 1
            risk_sum += entry.risk_score

            if entry.risk_score >= 0.7:
                high_risk.append(entry)
            if entry.status == AuditStatus.BLOCKED:
                blocked.append(entry)

        return AuditSummary(
            period_start=entries[-1].timestamp if entries else datetime.now(),
            period_end=entries[0].timestamp if entries else datetime.now(),
            total_events=len(entries),
            by_category=dict(by_category),
            by_status=dict(by_status),
            by_agent=dict(by_agent),
            high_risk_events=high_risk[:50],  # Máximo 50 eventos
            blocked_events=blocked[:50],
            avg_risk_score=risk_sum / len(entries) if entries else 0.0
        )

    def export_report(
            self,
            output_path: str,
            format: str = "json",
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None
    ) -> bool:
        """
        Exporta reporte de auditoría a archivo.

        Args:
            output_path: Ruta del archivo de salida
            format: Formato de exportación (json, csv)
            start_time: Inicio del período
            end_time: Fin del período

        Returns:
            True si la exportación fue exitosa
        """
        entries = self.get_entries(start_time=start_time, end_time=end_time, limit=100000)
        summary = self.get_summary(start_time=start_time, end_time=end_time)

        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            if format == "json":
                report = {
                    "exported_at": datetime.now().isoformat(),
                    "project_id": self.project_id,
                    "summary": summary.to_dict(),
                    "entries": [e.to_dict() for e in entries]
                }
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)

            elif format == "csv":
                import csv
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "timestamp", "event_id", "category", "action", "status",
                        "agent_name", "risk_score", "details"
                    ])
                    for entry in entries:
                        writer.writerow([
                            entry.timestamp.isoformat(),
                            entry.event_id,
                            entry.category.name,
                            entry.action,
                            entry.status.name,
                            entry.agent_name,
                            entry.risk_score,
                            json.dumps(entry.details)
                        ])

            logger.info(f"Audit report exported to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export audit report: {e}")
            return False

    def get_risk_assessment(self) -> Dict[str, Any]:
        """
        Genera evaluación de riesgo actual del proyecto.
        """
        # Obtener eventos de las últimas 24 horas
        start_time = datetime.now() - timedelta(hours=24)
        entries = self.get_entries(start_time=start_time, limit=1000)

        if not entries:
            return {
                "risk_level": "LOW",
                "risk_score": 0.0,
                "assessment": "No hay actividad reciente",
                "recommendations": ["El sistema está operando normalmente - sin eventos para analizar"]  # ✅ Agregado
            }

        # Calcular métricas de riesgo
        avg_risk = sum(e.risk_score for e in entries) / len(entries)
        blocked_count = sum(1 for e in entries if e.status == AuditStatus.BLOCKED)
        high_risk_count = sum(1 for e in entries if e.risk_score >= 0.7)

        # Determinar nivel de riesgo
        if avg_risk >= 0.8 or high_risk_count >= 10:
            risk_level = "CRITICAL"
        elif avg_risk >= 0.6 or high_risk_count >= 5:
            risk_level = "HIGH"
        elif avg_risk >= 0.4 or blocked_count >= 5:
            risk_level = "MEDIUM"
        elif avg_risk >= 0.2:
            risk_level = "LOW"
        else:
            risk_level = "MINIMAL"

        return {
            "risk_level": risk_level,
            "risk_score": round(avg_risk, 3),
            "assessment": f"Riesgo {risk_level} basado en {len(entries)} eventos en las últimas 24h",
            "metrics": {
                "total_events_24h": len(entries),
                "blocked_events": blocked_count,
                "high_risk_events": high_risk_count,
                "avg_risk_score": round(avg_risk, 3)
            },
            "recommendations": self._generate_recommendations(avg_risk, blocked_count, high_risk_count)
        }

    def _generate_recommendations(
            self,
            avg_risk: float,
            blocked_count: int,
            high_risk_count: int
    ) -> List[str]:
        """Genera recomendaciones basadas en métricas de riesgo"""
        recommendations = []

        if avg_risk >= 0.6:
            recommendations.append("Considerar reducir el nivel de autonomía del agente")

        if blocked_count >= 5:
            recommendations.append(
                "Revisar acciones bloqueadas frecuentemente - puede indicar configuración muy restrictiva o comportamiento anómalo")

        if high_risk_count >= 3:
            recommendations.append("Múltiples eventos de alto riesgo detectados - revisar configuración de seguridad")

        if not recommendations:
            recommendations.append("El sistema está operando dentro de parámetros normales")

        return recommendations

    def clear_entries(self) -> int:
        """Limpia todas las entradas en memoria (no archivos)"""
        with self._entries_lock:
            count = len(self._entries)
            self._entries.clear()
            self._counters.clear()
            self._risk_accumulator = 0.0
        logger.info(f"Cleared {count} audit entries from memory")
        return count

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas rápidas del auditor"""
        with self._entries_lock:
            return {
                "project_id": self.project_id,
                "entries_in_memory": len(self._entries),
                "audit_level": self.audit_level.name,
                "retention_days": self.retention_days,
                "alert_threshold": self.alert_threshold,
                "counters": dict(self._counters),
                "avg_risk": round(self._risk_accumulator / max(1, len(self._entries)), 3),
                "log_file": str(self._log_file),
                "alert_callbacks": len(self._alert_callbacks)
            }