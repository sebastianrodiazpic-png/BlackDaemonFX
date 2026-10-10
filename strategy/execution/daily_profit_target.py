"""Gestor de meta de ganancia diaria (Daily Profit Target Manager).

Permite parametrizar desde el dashboard una meta diaria de ganancia porcentual
(ej. 1%, 2%, 3%), bloqueando todas las nuevas entradas de los workers al cumplirse
la meta para proteger las ganancias obtenidas en la jornada.

Mantiene activas las posiciones abiertas con su gestión de riesgo (SL, TP, BE con
spread y swap). Ofrece la opción de desactivar la protección o desbloquearla
temporalmente ("ganar un poquito más") con una advertencia de riesgo explícita de
overtrading y pérdida de capital acumulado.

Reactivación automática:
Al comenzar la sesión de Asia del siguiente día de negociación (00:00 UTC / 09:00 JST),
el bloqueo se libera automáticamente y todos los workers retoman el escaneo sin
requerir intervención manual.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

logger = logging.getLogger(__name__)


RISK_WARNING_TEXT = (
    "ADVERTENCIA DE RIESGO DE OVERTRADING: Has alcanzado con éxito tu meta diaria. "
    "Continuar operando desafía la disciplina del plan de trading y aumenta "
    "significativamente el riesgo de sobreoperar, pagar spreads/swaps adicionales y devolver "
    "parte o la totalidad de las ganancias acumuladas hoy. ¿Confirmas que deseas asumir el riesgo?"
)


class DailyProfitTargetManager:
    """Administra la meta diaria de ganancia, bloqueos de entradas y reinicio en Asia."""

    def __init__(self, repository: Any, source: str = "DEMO"):
        self.repository = repository
        self.source = str(source or "DEMO").upper()

    def get_status(self, now_utc: datetime | None = None) -> dict[str, Any]:
        """Evalúa el estado actual de la meta diaria, calculando PnL, bloqueos y reinicios."""
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)
        elif now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=timezone.utc)

        today_str = now_utc.strftime("%Y-%m-%d")

        pref = self.repository.latest_daily_profit_target_preference(source=self.source)

        # -------------------------------------------------------------
        # 1. Verificación de reactivación automática en Sesión de Asia
        # -------------------------------------------------------------
        locked_date = pref.get("locked_date")
        asia_hour = int(pref.get("asia_session_start_hour_utc") or 0)

        # Si estuvo bloqueado en una fecha anterior y ya estamos en un nuevo día UTC (hora >= asia_hour)
        if locked_date and locked_date < today_str and now_utc.hour >= asia_hour:
            logger.info(
                "Sesión de Asia alcanzada (%s UTC). Reiniciando meta diaria automáticamente para %s.",
                now_utc.strftime("%Y-%m-%d %H:%M"),
                self.source,
            )
            pref = self.repository.save_daily_profit_target_preference(
                source=self.source,
                enabled=pref.get("enabled", True),
                target_percent=pref.get("target_percent", 2.0),
                extra_target_buffer_percent=pref.get("extra_target_buffer_percent", 1.0),
                is_target_reached=False,
                override_unlocked=False,
                locked_date=None,
                last_reset_date=today_str,
                asia_session_start_hour_utc=asia_hour,
            )
            try:
                if hasattr(self.repository, "save_audit_event"):
                    self.repository.save_audit_event(
                        "DAILY_TARGET_AUTO_RESET_ASIA_SESSION",
                        source=self.source,
                        action="AUTO_RESET_ASIA",
                        reason=f"Reactivación automática en sesión de Asia ({today_str} {now_utc.hour:02d}:00 UTC)",
                        payload={"locked_date_anterior": locked_date, "nuevo_dia": today_str},
                    )
            except Exception:
                pass

        # -------------------------------------------------------------
        # 2. Resumen del día y cálculo de retorno
        # -------------------------------------------------------------
        summary = self.repository.get_daily_closed_trades_summary(
            source=self.source,
            now_utc=now_utc,
        )

        daily_return_pct = float(summary.get("daily_return_pct") or 0.0)
        today_net_pnl = float(summary.get("today_net_pnl") or 0.0)
        target_percent = float(pref.get("target_percent") or 2.0)
        extra_buffer = float(pref.get("extra_target_buffer_percent") or 1.0)
        override_unlocked = bool(pref.get("override_unlocked", False))
        is_target_reached = bool(pref.get("is_target_reached", False))
        enabled = bool(pref.get("enabled", True))

        # Meta efectiva (si se desbloqueó para 'ganar un poco más', la meta aumenta en el buffer)
        effective_target = target_percent + extra_buffer if override_unlocked else target_percent

        # -------------------------------------------------------------
        # 3. Evaluación de cumplimiento de meta
        # -------------------------------------------------------------
        if enabled:
            if daily_return_pct >= effective_target:
                if not is_target_reached:
                    logger.info(
                        "Meta diaria alcanzada (+%.2f%% >= %.2f%%). Bloqueando nuevas entradas para %s.",
                        daily_return_pct,
                        effective_target,
                        self.source,
                    )
                    pref = self.repository.save_daily_profit_target_preference(
                        source=self.source,
                        enabled=True,
                        target_percent=target_percent,
                        extra_target_buffer_percent=extra_buffer,
                        is_target_reached=True,
                        override_unlocked=override_unlocked,
                        locked_date=today_str,
                        last_reset_date=pref.get("last_reset_date"),
                        asia_session_start_hour_utc=asia_hour,
                    )
                    is_target_reached = True
                    try:
                        if hasattr(self.repository, "save_audit_event"):
                            self.repository.save_audit_event(
                                "DAILY_TARGET_REACHED_LOCKED",
                                source=self.source,
                                action="LOCK_NEW_ENTRIES",
                                reason=(
                                    f"Meta diaria alcanzada: +{daily_return_pct:.2f}% "
                                    f"(objetivo {effective_target:.2f}%). Nuevas entradas bloqueadas."
                                ),
                                payload={
                                    "daily_return_pct": daily_return_pct,
                                    "effective_target": effective_target,
                                    "today_net_pnl": today_net_pnl,
                                },
                            )
                    except Exception:
                        pass

        is_locked = enabled and is_target_reached
        can_override = enabled and is_target_reached and not override_unlocked

        status_msg = (
            f"Meta diaria de {effective_target:.2f}% alcanzada (+{daily_return_pct:.2f}% hoy). "
            f"Entradas bloqueadas hasta la sesión de Asia (00:00 UTC)."
            if is_locked
            else (
                "Meta diaria desactivada (sin restricción de beneficio)."
                if not enabled
                else f"Operando normalmente. Meta: {effective_target:.2f}%, Actual: {daily_return_pct:.2f}%."
            )
        )

        return {
            "source": self.source,
            "enabled": enabled,
            "target_percent": round(target_percent, 2),
            "extra_target_buffer_percent": round(extra_buffer, 2),
            "effective_target_percent": round(effective_target, 2),
            "daily_return_pct": round(daily_return_pct, 2),
            "today_net_pnl": round(today_net_pnl, 2),
            "today_trades_count": summary.get("today_closed_trades_count", 0),
            "today_winning_trades": summary.get("today_winning_trades", 0),
            "today_losing_trades": summary.get("today_losing_trades", 0),
            "base_balance": round(float(summary.get("base_balance") or 0.0), 2),
            "current_balance": round(float(summary.get("current_balance") or 0.0), 2),
            "current_equity": round(float(summary.get("current_equity") or 0.0), 2),
            "is_target_reached": is_target_reached,
            "override_unlocked": override_unlocked,
            "locked_date": pref.get("locked_date"),
            "last_reset_date": pref.get("last_reset_date"),
            "asia_session_start_hour_utc": asia_hour,
            "is_locked": is_locked,
            "can_override": can_override,
            "risk_warning": RISK_WARNING_TEXT if is_locked else "",
            "status_message": status_msg,
        }

    def is_entry_allowed(self, now_utc: datetime | None = None) -> tuple[bool, str]:
        """Comprueba si está permitido colocar nuevas órdenes en este momento."""
        status = self.get_status(now_utc=now_utc)
        if status["is_locked"]:
            return False, status["status_message"]
        return True, "Entradas permitidas"

    def update_settings(
        self,
        enabled: bool,
        target_percent: float,
        extra_target_buffer_percent: float | None = None,
        now_utc: datetime | None = None,
    ) -> dict[str, Any]:
        """Actualiza la configuración de la meta diaria desde el dashboard."""
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)

        current = self.repository.latest_daily_profit_target_preference(source=self.source)
        target = max(0.1, float(target_percent if target_percent is not None else 2.0))
        buffer = (
            max(0.1, float(extra_target_buffer_percent))
            if extra_target_buffer_percent is not None
            else float(current.get("extra_target_buffer_percent") or 1.0)
        )

        # Si se desactiva, liberamos cualquier bloqueo previo
        is_target_reached = bool(current.get("is_target_reached", False))
        override_unlocked = bool(current.get("override_unlocked", False))
        locked_date = current.get("locked_date")

        if not enabled:
            is_target_reached = False
            override_unlocked = False
            locked_date = None

        pref = self.repository.save_daily_profit_target_preference(
            source=self.source,
            enabled=bool(enabled),
            target_percent=target,
            extra_target_buffer_percent=buffer,
            is_target_reached=is_target_reached,
            override_unlocked=override_unlocked,
            locked_date=locked_date,
            last_reset_date=current.get("last_reset_date"),
            asia_session_start_hour_utc=int(current.get("asia_session_start_hour_utc") or 0),
        )

        try:
            if hasattr(self.repository, "save_audit_event"):
                self.repository.save_audit_event(
                    "DAILY_TARGET_SETTINGS_CHANGED",
                    source=self.source,
                    action="UPDATE_SETTINGS",
                    reason=f"Ajuste de meta diaria: habilitado={enabled}, meta={target}%, buffer={buffer}%",
                    payload={"enabled": enabled, "target_percent": target, "buffer": buffer},
                )
        except Exception:
            pass

        return self.get_status(now_utc=now_utc)

    def request_override_more_profit(
        self,
        extra_percent: float = 1.0,
        now_utc: datetime | None = None,
    ) -> dict[str, Any]:
        """Desbloquea temporalmente las entradas tras confirmación del usuario para buscar más beneficio."""
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)

        current = self.repository.latest_daily_profit_target_preference(source=self.source)
        extra = max(0.1, float(extra_percent or 1.0))

        pref = self.repository.save_daily_profit_target_preference(
            source=self.source,
            enabled=True,
            target_percent=float(current.get("target_percent") or 2.0),
            extra_target_buffer_percent=extra,
            is_target_reached=False,
            override_unlocked=True,
            locked_date=current.get("locked_date"),
            last_reset_date=current.get("last_reset_date"),
            asia_session_start_hour_utc=int(current.get("asia_session_start_hour_utc") or 0),
        )

        try:
            if hasattr(self.repository, "save_audit_event"):
                self.repository.save_audit_event(
                    "DAILY_TARGET_OVERRIDE_UNLOCKED",
                    source=self.source,
                    action="OVERRIDE_MORE_PROFIT",
                    reason=(
                        f"El operador desbloqueó temporalmente nuevas entradas para buscar "
                        f"+{extra:.2f}% adicional, asumiendo el riesgo advertido de overtrading."
                    ),
                    payload={"extra_buffer_percent": extra},
                )
        except Exception:
            pass

        return self.get_status(now_utc=now_utc)
