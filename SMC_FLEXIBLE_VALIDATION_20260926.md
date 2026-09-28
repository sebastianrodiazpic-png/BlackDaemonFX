# Reglas flexibles SMC — 26 septiembre 2026

Sustituyen en la ruta multi-temporal las restricciones descritas en SMC_STRUCTURAL_VALIDATION_20260926.md.

## H1
Pivotes estrictos asimetricos: izquierda 3, derecha 1. Se utiliza la ultima pareja disponible; no se añade un criterio de antiguedad que el ejemplo no implementaba. Si falta un extremo o la pareja queda invertida, respaldo de maximo/minimo de exactamente 24 velas cerradas. Sin historial suficiente o con datos invalidos en ese respaldo, no se habilita rango. La entrada sigue requiriendo discount para BUY y premium para SELL dentro del rango; tambien se conserva la ubicacion del punto medio del OB en H1.

El proveedor ya descarta la vela abierta. Las funciones reciben exclusivamente velas cerradas y no eliminan una segunda vela. El resultado publica method y fallback_used.

## M15
Referencia: maximo/minimo de hasta 15 velas anteriores al origen del OB. Se admite cierre fuera del nivel (BOS) o extremo de mecha fuera del nivel (SWEEP), hasta 8 velas despues. SWEEP es la etiqueta del ejemplo para ruptura por mecha, no una nueva verificacion de barrido y recuperacion. El constructor evalua prefijos cerrados y conserva el requisito de desplazamiento; no acepta cualquier mecha como setup completo. Conserva invalidacion por cierre, caducidad y ubicacion H1. Se guardan calidad, nivel e indice.

## M5
FVG obligatorio, ahora desacoplado de la vela exacta del CHoCH. Las tres velas del FVG deben estar dentro del intervalo inclusivo CHoCH-3 a CHoCH+3. La busqueda solo alcanza la vela cerrada de confirmacion. El CHoCH del mismo setup puede estar hasta 3 velas antes de esa confirmacion. No se usa una vela futura ni se retrodata una entrada cuando aparece el gap. Se conservan antiguedad, relleno previo y alineacion configurados en el detector existente, asi como las demas condiciones de entrada.

## Configuracion
PipelineConfig: h1_fractal_left=3, h1_fractal_right=1, h1_fallback_bars=24, m15_flexible_structure=True, m15_impulse_bars=8, m5_choch_fvg_window=3. El validador M15 estricto sigue disponible con m15_flexible_structure=False para comparaciones. Los helpers simetricos originales permanecen disponibles, pero H1 activo usa la funcion flexible.

No se cambiaron los limites de riesgo ni se enviaron ordenes o reiniciaron bots. Los workers existentes requieren reinicio para garantizar que carguen estas reglas. Las pruebas verifican logica y causalidad, no rendimiento financiero.
