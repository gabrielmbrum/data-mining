import polars as pl


FUEL_TYPES_MAP = {
    "g": "Gasoline",
    "d": "Diesel",
    "f": "Flex",
    "e": "Ethanol",
    "h": "Hybrid",
    "l": "Electric",
    "n": "Natural Gas",
}


# ==========================================
# PREPROCESSING
# ==========================================


def clean_data(df: pl.DataFrame) -> pl.DataFrame:
    """
    Removes duplicate records and rows with a zero monetary value.

    This function evaluates the initial height of the DataFrame, drops completely
    duplicated rows while keeping the first occurrence, filters out any records where
    the price ('valor_centavos') is equal to zero, and prints the count of removed
    records at each step to track data loss.
    """
    print(f"Initial DataFrame size: {df.height:,} records")

    raw_total = df.height
    df = df.unique(subset=df.columns, keep="first")
    cooked_total = df.height
    print(f"Duplicate records removed: {raw_total - cooked_total:,}")

    total_before = df.height
    df = df.filter(pl.col("valor_centavos") != 0)
    non_zero_total = df.height
    print(
        f"Records with zero 'valor_centavos' removed: {total_before - non_zero_total:,}"
    )

    return df


def filter_relevant_brands(df: pl.DataFrame) -> pl.DataFrame:
    """
    Filters the dataset to keep only highly relevant vehicle brands based on portfolio size.

    The function identifies unique vehicles by combining brand, FIPE code, model year,
    and fuel type to avoid temporal accumulation bias. It then aggregates the total number
    of unique vehicles and the total number of electrified unique vehicles (hybrid or electric)
    per brand. Only brands with more than 30 unique vehicles overall, or at least 15
    electrified vehicles (l or h), are kept in the final dataset.
    """
    unique_vehicles_df = df.select(
        ["nome_marca", "codigo_fipe", "ano_modelo", "sigla_combustivel"]
    ).unique()

    brand_stats = unique_vehicles_df.group_by("nome_marca").agg(
        [
            pl.len().alias("total_unique"),
            pl.col("sigla_combustivel")
            .is_in(["h", "l"])
            .sum()
            .alias("total_electrified"),
        ]
    )

    valid_brands = brand_stats.filter(
        (pl.col("total_unique") > 30) | (pl.col("total_electrified") >= 15)
    )["nome_marca"].to_list()

    filtered_df = df.filter(pl.col("nome_marca").is_in(valid_brands))

    print(f"Brands kept after filtering: {len(valid_brands)}")
    return filtered_df


def filter_by_release_year(df: pl.DataFrame, max_age: int = 20) -> pl.DataFrame:
    """
    Filters out vehicles older than a specified maximum age based on their true launch year.

    This function restricts the dataset to a specific cohort by ensuring that only
    vehicles released within the last 'max_age' years (relative to 2026) are kept.
    """
    raw_total = df.height

    df = df.filter(pl.col("ano_lancamento") >= 2026 - max_age)

    cooked_total = df.height
    print(
        f"Records with release year older than {2026 - max_age} removed: {raw_total - cooked_total:,}"
    )
    return df


def preprocess_data(df: pl.DataFrame) -> pl.DataFrame:
    """
    Executes the main data preprocessing pipeline.

    Transforms temporal data to a strict monthly resolution by identifying
    the exact launch date (year and month) for each cohort and calculating
    the age in months ('idade_meses') to increase the time-series density.
    """
    raw_total = df.height
    df = df.filter(pl.col("tipo_veiculo") == "carro")
    cooked_total = df.height
    print(f"Records with tipo_veiculo != 'carro' removed: {raw_total - cooked_total:,}")

    df = df.with_columns(
        pl.date(pl.col("ano_referencia"), pl.col("mes_referencia"), 1).alias(
            "data_referencia"
        )
    ).drop(["ano_referencia", "mes_referencia"])

    df = df.with_columns(
        pl.when(pl.col("zero_km") == True)
        .then(pl.col("data_referencia").dt.year())
        .otherwise(pl.col("ano_modelo"))
        .alias("ano_modelo")
    )

    # ---------------------------------------------------------
    # RESOLUÇÃO MENSAL: Cálculo da data absoluta e idade em meses
    # ---------------------------------------------------------
    cohort_keys = ["codigo_fipe", "ano_modelo", "sigla_combustivel"]

    # Encontra o primeiro mês absoluto de cotação de cada veículo
    df = df.with_columns(
        pl.col("data_referencia").min().over(cohort_keys).alias("data_lancamento")
    )

    # Extrai o ano de lançamento para o filtro da coorte (max_age)
    df = df.with_columns(pl.col("data_lancamento").dt.year().alias("ano_lancamento"))

    # idade em anos
    df = df.with_columns(
        (pl.col("data_referencia").dt.year() - pl.col("ano_lancamento")).alias(
            "idade_anos"
        )
    )

    # Calcula a idade em meses exatos de diferença
    df = df.with_columns(
        (
            (pl.col("data_referencia").dt.year() - pl.col("data_lancamento").dt.year())
            * 12
            + (
                pl.col("data_referencia").dt.month()
                - pl.col("data_lancamento").dt.month()
            )
        ).alias("idade_meses")
    )

    df = df.drop(["tipo_veiculo", "valor_formatado", "nome_combustivel", "zero_km"])
    df = df.filter(
        (pl.col("sigla_combustivel") != "n") & (pl.col("sigla_combustivel") != "e")
    )
    df = filter_relevant_brands(df)
    df = filter_by_release_year(df, max_age=20)

    return df


def calculate_value_retention(df: pl.DataFrame) -> pl.DataFrame:
    """
    Calculates the Value Retention Rate (VRR) anchored at month zero.

    Uses 'idade_meses == 0' to pinpoint the absolute launch price without
    chronological ambiguity.
    """
    print("\n--- Calculating Value Retention Rate (VRR) ---")

    cohort_keys = ["codigo_fipe", "ano_modelo", "sigla_combustivel"]

    # Isola o mês exato de estreia (idade_meses == 0)
    df_base_price = (
        df.filter(pl.col("idade_meses") == 0)
        .group_by(cohort_keys)
        .first()
        .select(cohort_keys + [pl.col("valor_centavos").alias("preco_lancamento")])
    )

    initial_count = df.height
    df = df.join(df_base_price, on=cohort_keys, how="inner")
    final_count = df.height

    print(
        f"Registos retidos com preço de lançamento absoluto (t=0): {final_count:,} (de {initial_count:,})"
    )

    df = df.with_columns(
        (pl.col("valor_centavos") / pl.col("preco_lancamento")).alias("taxa_retencao")
    )

    return df
