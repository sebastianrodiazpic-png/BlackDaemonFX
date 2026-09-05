"""Puntuacion de calidad de un Order Block (LEGADO / SIN USO).

Sistema de scoring por checklist ponderado que califica un OB de 0 a 100 y le
asigna un grado (A+, A, B, C, REJECT). Es el ANTECESOR del scoring que hoy
usa el bot en `strategy.smc.confirmation_engine`, donde el calculo es mas rico
(incluye patrones chartistas, divergencias, armonicos y penalizaciones por
conflicto).

ESTADO: no lo importa NINGUN modulo del proyecto, ni de produccion ni de
tests. Se conserva como referencia historica. Ojo al depurar: sus umbrales de
grado NO coinciden con los del motor vivo. Aqui A+ empieza en 85, mientras que
en `confirmation_engine._grade` A+ empieza en 90. Si ves un grado en la
bitacora, viene del confirmation engine, no de este modulo.

Vinculaciones:
- Ninguna. Solo depende de pandas.
"""

import pandas as pd


def calculate_ob_displacement(
    df,
    ob_time,
    ob_type,
    lookforward=10
):
    """Mide cuanto se desplazo el precio a favor tras formarse el OB (LEGADO).

    El desplazamiento es la prueba de que hubo intencion institucional: un OB
    seguido de un movimiento amplio vale mas que uno seguido de lateralidad.

    Proceso: localiza la vela del OB por su marca de tiempo exacta, toma las
    `lookforward` velas siguientes y mide el recorrido maximo a favor respecto
    del cierre del OB.

    Args:
        df: DataFrame OHLC con columna `time`.
        ob_time: marca de tiempo exacta de la vela del OB.
        ob_type: `"bullish"` o `"bearish"`.
        lookforward: cuantas velas posteriores se miden.

    Returns:
        La distancia en precio, nunca negativa. Devuelve `0.0` en todos los
        casos degradados: DataFrame vacio, `ob_time` no encontrado, sin velas
        posteriores o `ob_type` desconocido. Es decir, un `0.0` significa
        "sin desplazamiento" pero tambien "no se pudo medir".

    Vinculaciones:
    - Ninguna: funcion sin llamadores en el proyecto.
    """
    if df.empty:

        return 0.0

    data = df.copy()

    data["time"] = pd.to_datetime(
        data["time"],
        utc=True
    )

    data = (
        data
        .sort_values("time")
        .reset_index(drop=True)
    )

    positions = data.index[
        data["time"] == pd.to_datetime(
            ob_time,
            utc=True
        )
    ]

    if len(positions) == 0:

        return 0.0

    index = positions[0]

    future = data.iloc[
        index + 1:
        index + 1 + lookforward
    ]

    if future.empty:

        return 0.0

    ob_close = float(
        data.iloc[index]["close"]
    )

    if ob_type == "bullish":

        max_price = float(
            future["high"].max()
        )

        return max(
            0.0,
            max_price - ob_close
        )

    elif ob_type == "bearish":

        min_price = float(
            future["low"].min()
        )

        return max(
            0.0,
            ob_close - min_price
        )

    return 0.0


def calculate_average_range(
    df,
    period=20
):
    """Calcula el rango medio (high - low) de las ultimas velas (LEGADO).

    Sirve como referencia de volatilidad para decidir si un desplazamiento es
    "fuerte": se compara el resultado de `calculate_ob_displacement` contra
    este promedio.

    Args:
        df: DataFrame OHLC.
        period: numero de velas finales a promediar.

    Returns:
        El rango medio como float, o `0.0` si no hay datos.

    Vinculaciones:
    - Ninguna: funcion sin llamadores en el proyecto.
    """
    if df.empty:

        return 0.0

    data = df.copy()

    ranges = (
        data["high"].astype(float)
        -
        data["low"].astype(float)
    )

    recent_ranges = ranges.tail(period)

    if recent_ranges.empty:

        return 0.0

    return float(
        recent_ranges.mean()
    )


def calculate_ob_score(
    trend_aligned=False,
    correct_zone=False,
    liquidity_sweep=False,
    choch=False,
    bos=False,
    strong_displacement=False,
    fresh=True,
    retest_clean=False,
    micro_confirmation=False
):
    """Suma la puntuacion de calidad de un OB segun su checklist (LEGADO).

    Reparto de pesos, que suma exactamente 100:
    tendencia alineada 20, zona correcta 15, barrido de liquidez 15,
    CHOCH 10, BOS 10, desplazamiento fuerte 10, OB fresco 10,
    retest limpio 5, confirmacion micro 5.

    A diferencia del motor vivo, aqui los pesos SI suman 100, asi que el
    `min(score, 100)` final nunca llega a recortar nada.

    Args:
        trend_aligned: el OB va a favor de la tendencia.
        correct_zone: OB alcista en discount u OB bajista en premium.
        liquidity_sweep: hubo barrido de liquidez previo.
        choch: la ruptura que valido el OB fue un cambio de caracter.
        bos: la ruptura fue una continuacion de estructura.
        strong_displacement: el movimiento posterior fue amplio.
        fresh: el OB no ha sido tocado mas veces de las permitidas. Es el
            unico parametro que por defecto vale `True`.
        retest_clean: el retest fue limpio.
        micro_confirmation: hubo confirmacion en timeframe menor.

    Returns:
        Entero de 0 a 100.

    Vinculaciones:
    - Lo llama `evaluate_order_block` en este mismo modulo. Sin llamadores
      fuera del fichero.
    """
    score = 0

    if trend_aligned:
        score += 20

    if correct_zone:
        score += 15

    if liquidity_sweep:
        score += 15

    if choch:
        score += 10

    if bos:
        score += 10

    if strong_displacement:
        score += 10

    if fresh:
        score += 10

    if retest_clean:
        score += 5

    if micro_confirmation:
        score += 5

    return min(score, 100)


def get_ob_grade(score):
    """Traduce la puntuacion numerica del OB a una letra (LEGADO).

    Cortes: A+ >= 85, A >= 70, B >= 60, C >= 40, por debajo `REJECT`.

    ATENCION: estos cortes NO son los del motor en produccion. En
    `strategy.smc.confirmation_engine._grade` el A+ exige 90. No compares
    grados de los dos sistemas como si fueran equivalentes.

    Args:
        score: puntuacion 0-100.

    Returns:
        `"A+"`, `"A"`, `"B"`, `"C"` o `"REJECT"`.

    Vinculaciones:
    - Lo llama `evaluate_order_block` en este mismo modulo.
    """
    score = float(score)

    if score >= 85:
        return "A+"

    if score >= 70:
        return "A"

    if score >= 60:
        return "B"

    if score >= 40:
        return "C"

    return "REJECT"


def evaluate_order_block(
    trend_aligned=False,
    correct_zone=False,
    liquidity_sweep=False,
    choch=False,
    bos=False,
    strong_displacement=False,
    ob_touches=0,
    retest_clean=False,
    micro_confirmation=False,
    max_touches=1
):
    """Evalua un OB completo y dictamina si es operable (LEGADO).

    Punto de entrada del modulo: deriva la frescura a partir del numero de
    toques, calcula la puntuacion con `calculate_ob_score`, la convierte a
    grado con `get_ob_grade` y decide la validez final.

    Un OB es valido solo si es fresco Y su grado no es `REJECT`. La frescura
    es condicion necesaria: un OB muy tocado queda invalidado por bueno que
    sea su score.

    Args:
        trend_aligned, correct_zone, liquidity_sweep, choch, bos,
        strong_displacement, retest_clean, micro_confirmation: banderas del
            checklist, ver `calculate_ob_score`.
        ob_touches: cuantas veces el precio ya visito la zona.
        max_touches: toques maximos tolerados para seguir considerandolo
            fresco.

    Returns:
        Dict con `ob_score`, `ob_grade`, `ob_fresh`, `ob_touches` y
        `ob_valid`.

    Vinculaciones:
    - Ninguna fuera de este fichero: sin llamadores en el proyecto. La
      decision equivalente en produccion la toma
      `strategy.smc.confirmation_engine.evaluate_m5_confirmation`.
    """
    fresh = (
        ob_touches <= max_touches
    )

    score = calculate_ob_score(
        trend_aligned=trend_aligned,
        correct_zone=correct_zone,
        liquidity_sweep=liquidity_sweep,
        choch=choch,
        bos=bos,
        strong_displacement=strong_displacement,
        fresh=fresh,
        retest_clean=retest_clean,
        micro_confirmation=micro_confirmation
    )

    grade = get_ob_grade(score)

    return {
        "ob_score": score,
        "ob_grade": grade,
        "ob_fresh": fresh,
        "ob_touches": int(ob_touches),
        "ob_valid": (
            fresh
            and grade != "REJECT"
        )
    }