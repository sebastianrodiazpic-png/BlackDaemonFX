# SMC: rango H1, estructura M15 y FVG M5

Implementado en la ruta multi-temporal H1_LOCATION_ONLY existente.

- H1 usa los ultimos pivotes estrictos confirmados (5 velas a cada lado). El proveedor elimina la vela abierta antes del calculo. Sin ambos pivotes, o con limites invertidos, no hay rango valido; no se sustituye por 100 velas. El precio fuera del rango o en equilibrio no habilita direccion. No se exige tendencia H1.
- M15 mantiene desplazamiento y exige ruptura por cierre de un pivote de 3 velas a cada lado, ya confirmado al cierre del OB. La ruptura debe producirse en las siguientes 6 velas; no vale un nivel ya roto antes del OB. Se registra nivel e indice de ruptura sin atribuir una clasificacion BOS/CHoCH que requeriria determinar la tendencia previa.
- La ubicacion del OB se comprueba por su punto medio respecto al rango H1 actual. Ya no se exige discount/premium local M15. H1_PRIMARY se mantiene.
- M5 exige un CHoCH real del mismo setup en la vela de confirmacion o las dos anteriores y un FVG cuya vela central o final sea ese CHoCH. Solo se examinan velas cerradas disponibles hasta la confirmacion. La ausencia bloquea tanto modo estricto como adaptativo. Se conserva la comprobacion existente de antiguedad y relleno anterior a la confirmacion del FVG.
- Los patrones chartistas conservan su puntuacion diagnostica, pero dejan de ser requisitos o vetos independientes en esta ruta. Se mantienen sweep, retesteo, desplazamiento, tolerancia y controles de riesgo/obstaculos.

El ejemplo recibido no era un reemplazo compatible del motor: asumía CHoCH por posicion, podia confirmar pivotes con una vela abierta y alcanzaba 85 puntos aun sin FVG. Se integraron condiciones en el motor existente.

Los tests validan comportamiento y causalidad; no prueban mayor rentabilidad ni flujo institucional. No se reinician procesos ni se envian ordenes. Los procesos existentes cargaran la nueva logica al reiniciarse. Antes de evaluar rendimiento hacen falta replay/backtest comparativo y demo con costes.
