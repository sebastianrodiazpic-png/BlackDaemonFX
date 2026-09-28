# ORB: SL/TP fijos — 2026-09-22

ORB_NEW_YORK queda excluido del cierre por invalidación del análisis, break-even,
profit-lock y extensión/cierre discrecional del runner. Los guardas reconocen
la estrategia y el perfil ORB para cubrir posiciones recuperadas tras reiniciar.
La auditoría de análisis continúa sin autorizar modificaciones de la posición.

Las entradas divididas conservan sus TP iniciales (TP1 y TP2); no se convierten
en una sola posición. La extensión del runner ya no cambia el TP planificado.
Las nuevas entradas registran exit_policy=ORB_FIXED_SL_TP y break_even_enabled=false.

Se conservan los rollback técnicos de ejecución y el cierre de emergencia por
exceso de riesgo post-fill. Por tanto, esta política excluye salidas discrecionales
de estrategia, pero no garantiza ausencia absoluta de cierres de emergencia.

Requiere reiniciar el worker ORB. Las posiciones existentes conservan el SL/TP que
ya tienen en MT5; no se revierte un SL modificado anteriormente ni se amplía riesgo.
No se han enviado órdenes ni reiniciado procesos durante esta modificación.

Pruebas: tests/test_orb_fixed_exits.py verifica exclusión directa y en monitor,
posiciones heredadas, todos los tramos y preservación de otras estrategias.

Validacion: 45 pruebas aprobadas (ORB, momentum, invalidacion y politica TP2).
La suite historica test_v65_smc_two_leg_tp3_protection conserva 7 fallos por expectativas 3R/4R y gestion sintetica antiguas; los mismos 7 fallos se reprodujeron desactivando el nuevo guarda ORB solo en el proceso de pruebas.
