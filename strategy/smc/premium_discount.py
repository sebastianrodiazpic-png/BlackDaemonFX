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
    """

    if order_blocks.empty:
        return order_blocks.copy()

    result = order_blocks[
        (order_blocks["ob_type"] == "bearish")
        & (order_blocks["zone"] == "premium")
    ].copy()

    return result