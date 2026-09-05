"""Zonas Premium / Discount / Equilibrium sobre el rango reciente.

Principio SMC: comprar barato y vender caro dentro del rango. Solo se compra en
zona `discount` (mitad inferior) y solo se vende en zona `premium` (mitad
superior). Evita perseguir el precio en el extremo equivocado del rango.

Vinculaciones:
- Es importado por `strategy.execution.trade_pipeline.run_pipeline`, que usa
  `calculate_premium_discount` para rellenar la casilla `premium_discount_ok`
  del checklist y para publicar `zone` y `equilibrium` en cada setup.
- No importa ningun otro modulo del proyecto: solo depende de pandas.
"""

import pandas as pd


def calculate_premium_discount(
    df: pd.DataFrame,
    lookback: int = 100
) -> pd.DataFrame:
    """
    Calcula las zonas Premium, Discount y Equilibrium.

    Para cada vela:
    - Busca el máximo y mínimo del rango usando un lookback.
    - Calcula el Equilibrium en el 50%.
    - Precio bajo el 50% = Discount.
    - Precio sobre el 50% = Premium.

    Parámetros:
        df: DataFrame con columnas high y low.
        lookback: Número de velas hacia atrás para calcular el rango.

    Retorna:
        DataFrame con las columnas:
        range_high
        range_low
        equilibrium
        zone

    Notas de implementacion:
    - Usa ventana deslizante con `min_periods=1`, asi que las primeras velas
      calculan su rango con menos historial del solicitado en vez de quedar
      como NaN.
    - La zona NO se decide con el cierre sino con el punto medio de la vela
      (`price_position = (high + low) / 2`).
    - Tambien anade la columna auxiliar `price_position`, no listada arriba.

    Vinculaciones:
    - La columna `zone` la consumen `is_bullish_ob_in_discount` y
      `is_bearish_ob_in_premium` de este mismo modulo, y el checklist de
      `strategy.execution.trade_pipeline`.
    """

    df = df.copy()

    # Máximo del rango
    df["range_high"] = (
        df["high"]
        .rolling(window=lookback, min_periods=1)
        .max()
    )

    # Mínimo del rango
    df["range_low"] = (
        df["low"]
        .rolling(window=lookback, min_periods=1)
        .min()
    )

    # Punto medio del rango: 50%
    df["equilibrium"] = (
        df["range_high"] + df["range_low"]
    ) / 2

    # Precio de referencia para determinar la zona
    df["price_position"] = (
        df["high"] + df["low"]
    ) / 2

    # Clasificación inicial
    df["zone"] = "equilibrium"

    # Discount: debajo del 50%
    df.loc[
        df["price_position"] < df["equilibrium"],
        "zone"
    ] = "discount"

    # Premium: sobre el 50%
    df.loc[
        df["price_position"] > df["equilibrium"],
        "zone"
    ] = "premium"

    return df


def is_bullish_ob_in_discount(
    order_blocks: pd.DataFrame
) -> pd.DataFrame:
    """
    Filtra Bullish Order Blocks ubicados en Discount.

    Aplica la regla "comprar barato": conserva solo los OB alcistas que caen
    en la mitad inferior del rango. Devuelve siempre una copia, de modo que el
    DataFrame original nunca se muta.

    Args:
        order_blocks: DataFrame de OB que debe traer las columnas `ob_type` y
            `zone` (esta ultima la anade `calculate_premium_discount`).

    Returns:
        Copia filtrada con los OB alcistas en discount. Si la entrada esta
        vacia devuelve una copia vacia sin fallar.
    """

    if order_blocks.empty:
        return order_blocks.copy()

    result = order_blocks[
        (order_blocks["ob_type"] == "bullish")
        & (order_blocks["zone"] == "discount")
    ].copy()

    return result


def is_bearish_ob_in_premium(
    order_blocks: pd.DataFrame
) -> pd.DataFrame:
    """
    Filtra Bearish Order Blocks ubicados en Premium.

    Contrapartida bajista de `is_bullish_ob_in_discount`: aplica la regla
    "vender caro" conservando solo los OB bajistas de la mitad superior del
    rango. Devuelve siempre una copia.

    Args:
        order_blocks: DataFrame de OB con las columnas `ob_type` y `zone`.

    Returns:
        Copia filtrada con los OB bajistas en premium. Si la entrada esta
        vacia devuelve una copia vacia sin fallar.
    """

    if order_blocks.empty:
        return order_blocks.copy()

    result = order_blocks[
        (order_blocks["ob_type"] == "bearish")
        & (order_blocks["zone"] == "premium")
    ].copy()

    return result