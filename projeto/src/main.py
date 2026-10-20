import os
import polars as pl
from pathlib import Path
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"

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


# ==========================================
# EXPLORATORY DATA ANALYSIS (EDA)
# ==========================================


def view_dataframe(df: pl.DataFrame, sample_size: int = 5) -> None:
    """
    Prints a quick overview of the DataFrame including schema, a data sample, and dimensions.

    This function is used for exploratory purposes to inspect the available columns,
    glimpse the data types, display a random sample of rows, and output the total number
    of records and columns.
    """
    print(df.columns)
    print(df.glimpse())
    print(df.sample(sample_size))
    print(f"\nTotal records: {df.height:,}")
    print(f"Total columns: {df.width:,}")


def analyze_unique_vehicles_by_brand_and_fuel(df: pl.DataFrame) -> pl.DataFrame:
    """
    Calculates and prints the real catalog size of unique vehicles per brand and fuel type.

    This function isolates unique vehicle entries based on brand, FIPE code, model year,
    and fuel type to ignore temporal accumulation bias. It replaces fuel acronyms with full
    names, groups the data, and pivots it into a wide format showing the unique count
    of vehicles for each fuel type alongside a row total, sorted by the largest portfolio.
    """
    unique_vehicles_df = df.select(
        ["nome_marca", "codigo_fipe", "ano_modelo", "sigla_combustivel"]
    ).unique()

    temp_df = unique_vehicles_df.with_columns(
        pl.col("sigla_combustivel")
        .replace(FUEL_TYPES_MAP, default=pl.col("sigla_combustivel"))
        .alias("nome_combustivel")
    )

    grouped_df = temp_df.group_by(["nome_marca", "nome_combustivel"]).len(
        name="unique_vehicles_count"
    )

    pivot_df = grouped_df.pivot(
        values="unique_vehicles_count", index="nome_marca", on="nome_combustivel"
    ).fill_null(0)

    fuel_columns = [col for col in pivot_df.columns if col != "nome_marca"]

    final_df = pivot_df.with_columns(
        pl.sum_horizontal(fuel_columns).alias("total_unique")
    ).sort("total_unique", descending=True)

    print("\n--- Real Catalog: Unique Vehicles by Brand and Fuel Type ---")
    with pl.Config(tbl_rows=-1, tbl_cols=-1):
        print(final_df)

    return final_df


def plot_vehicle_age_distribution(df: pl.DataFrame, output_dir: Path) -> None:
    """
    Plots a stacked bar chart showing the distribution of vehicle ages across
    the dataset, segmented by fuel type.

    This function aggregates the dataset by vehicle age and fuel type, pivots
    the data, and generates a stacked bar chart using Matplotlib. The resulting
    figure is saved as a PNG file in the specified output directory.
    """
    # Group by age AND fuel type
    grouped_df = df.group_by(["idade_anos", "sigla_combustivel"]).len(name="quantity")

    # Pivot the table so each fuel type becomes a column
    pivot_df = (
        grouped_df.pivot(values="quantity", index="idade_anos", on="sigla_combustivel")
        .fill_null(0)
        .sort("idade_anos")
    )

    print("\n--- Record Count by Vehicle Age and Fuel Type ---")
    with pl.Config(tbl_rows=20, tbl_cols=-1):
        print(pivot_df)

    ages = pivot_df["idade_anos"].to_list()

    fig, ax = plt.subplots(figsize=(10, 6))

    # Standard colors matching the temporal distribution chart
    colors = {
        "g": "#1f77b4",  # Blue
        "d": "#ff7f0e",  # Orange
        "f": "#2ca02c",  # Green
        "h": "#17becf",  # Cyan
        "l": "#d62728",  # Red
    }

    # Initialize the bottom array with zeros for the stacked bars
    bottoms = [0] * len(ages)

    # Iterate over the defined fuels to ensure a consistent stacking order
    for acronym, name in FUEL_TYPES_MAP.items():
        if acronym in pivot_df.columns:
            counts = pivot_df[acronym].to_list()
            ax.bar(
                ages,
                counts,
                bottom=bottoms,
                label=name,
                color=colors.get(acronym, "gray"),
                edgecolor="black",
                linewidth=0.5,
                alpha=0.85,
            )
            # Update the bottom values for the next fuel type
            bottoms = [b + c for b, c in zip(bottoms, counts)]

    # ax.set_title(
    #     "Distribution of Vehicle Age by Fuel Type", fontsize=13, fontweight="bold"
    # )
    ax.set_xlabel("Vehicle Age (Years)", fontsize=11)
    ax.set_ylabel("Number of Records", fontsize=11)

    if ages:
        ax.set_xticks(range(min(ages), max(ages) + 1, 2))

    ax.grid(axis="y", linestyle=":", alpha=0.7)

    # Add the legend
    ax.legend(title="Fuel Type", loc="upper right")

    plt.tight_layout()

    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / "vehicle_age_distribution.png"
    plt.savefig(file_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Chart successfully saved: {file_path}")


def plot_temporal_distribution(df: pl.DataFrame, output_dir: Path) -> None:
    """
    Plots the temporal distribution of records per fuel type over reference years.

    The function groups the records by the reference date's year and fuel type, pivots
    the data to have fuel types as columns, and computes a general total per year.
    It then plots and saves two line charts (one in linear scale, one in logarithmic scale)
    showing the evolution of data availability for each fuel category over time.
    """
    grouped_df = (
        df.with_columns(pl.col("data_referencia").dt.year().alias("year"))
        .group_by(["year", "sigla_combustivel"])
        .len(name="quantity")
        .sort("year")
    )

    pivot_df = (
        grouped_df.pivot(values="quantity", index="year", on="sigla_combustivel")
        .fill_null(0)
        .sort("year")
    )

    print("\n--- Record Count by Year and Fuel Type ---")
    with pl.Config(tbl_rows=-1, tbl_cols=-1):
        print(pivot_df)

    styles = {
        "g": ("Gasoline (g)", "#1f77b4", "--", "o"),
        "d": ("Diesel (d)", "#ff7f0e", "--", "s"),
        "f": ("Flex (f)", "#2ca02c", "-.", "^"),
        "e": ("Ethanol (e)", "#9467bd", ":", "v"),
        "h": ("Hybrid (h)", "#17becf", "-", "D"),
        "l": ("Electric (l)", "#d62728", "-", "*"),
        "n": ("Natural Gas (n)", "#7f7f7f", ":", "x"),
    }

    years = pivot_df["year"].to_list()
    fuel_columns = [col for col in pivot_df.columns if col != "year"]
    total_per_year = (
        pivot_df.select(pl.sum_horizontal(fuel_columns)).to_series().to_list()
    )

    configurations = [
        (False, "temporal_distribution_linear.png"),
        (True, "temporal_distribution_log.png"),
    ]

    for is_log, file_name in configurations:
        fig, ax = plt.subplots(figsize=(9, 6))

        ax.plot(
            years,
            total_per_year,
            label="Overall Total",
            color="black",
            linestyle="-",
            linewidth=2.5,
            alpha=0.8,
        )

        for acronym, (label, color, line_style, marker) in styles.items():
            if acronym in pivot_df.columns:
                values = pivot_df[acronym].to_list()
                if is_log:
                    values = [v if v > 0 else None for v in values]

                thickness = 2.2 if acronym in ["l", "h"] else 1.5

                ax.plot(
                    years,
                    values,
                    label=label,
                    color=color,
                    linestyle=line_style,
                    marker=marker,
                    markersize=5,
                    linewidth=thickness,
                )

        ax.set_xlabel("Reference Year", fontsize=11)
        ax.grid(True, which="both", linestyle=":", alpha=0.6)

        if is_log:
            ax.set_yscale("log")
            # ax.set_title(
            #     "Temporal Distribution by Fuel Type (Logarithmic Scale)",
            #     fontsize=12,
            #     fontweight="bold",
            # )
            ax.set_ylabel("Number of Records (Log Scale)", fontsize=11)
        else:
            # ax.set_title(
            #     "Temporal Distribution by Fuel Type (Linear Scale)",
            #     fontsize=12,
            #     fontweight="bold",
            # )
            ax.set_ylabel("Number of Records", fontsize=11)

        ax.legend(
            loc="upper left", bbox_to_anchor=(1.02, 1), frameon=True, title="Fuel Type"
        )

        plt.tight_layout()
        file_path = output_dir / file_name
        plt.savefig(file_path, dpi=300, bbox_inches="tight")
        print(f"Chart successfully saved: {file_path}")
        plt.close(fig)


def analyze_recent_concentration(df: pl.DataFrame, output_dir: Path) -> None:
    """
    Investigates whether the high volume of recent records is due to new portfolio launches
    or simply a higher update/tracking frequency in the FIPE dataset.
    """
    # 1. Group by model year and calculate key metrics
    analysis_df = (
        df.group_by("ano_modelo")
        .agg(
            [
                pl.len().alias("total_raw_records"),
                pl.struct(["codigo_fipe", "sigla_combustivel"])
                .n_unique()
                .alias("unique_vehicles_count"),
            ]
        )
        .with_columns(
            (pl.col("total_raw_records") / pl.col("unique_vehicles_count")).alias(
                "avg_months_tracked"
            )
        )
        .sort("ano_modelo")
    )

    print("\n--- Recent Records Concentration Overview by Model Year ---")
    with pl.Config(tbl_rows=20):
        print(analysis_df)

    # 2. Extract data for plotting
    years = analysis_df["ano_modelo"].to_list()
    unique_counts = analysis_df["unique_vehicles_count"].to_list()
    tracking_rates = analysis_df["avg_months_tracked"].to_list()

    # 3. Plot the results in subplots
    # Removed sharex=True so ax1 retains its own x-axis labels
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # Top Plot: Portfolio Diversity (Unique Vehicles)
    ax1.bar(years, unique_counts, color="#2ca02c", edgecolor="black", alpha=0.8)
    ax1.set_title(
        "Real Portfolio Growth (Unique Vehicles Launched per Year)",
        fontsize=12,
        fontweight="bold",
    )
    ax1.set_xlabel("Model Year", fontsize=11)
    ax1.set_ylabel("Unique Vehicles Count", fontsize=11)
    ax1.grid(axis="y", linestyle=":", alpha=0.7)

    # Adjust X-axis ticks for the top plot
    if years:
        ax1.set_xticks(range(min(years), max(years) + 1, 2))

    # Bottom Plot: FIPE Update Rate
    ax2.plot(years, tracking_rates, color="#d62728", marker="o", linewidth=2.5)
    ax2.set_title(
        "Update Frequency (Average Months Tracked per Vehicle)",
        fontsize=12,
        fontweight="bold",
    )
    ax2.set_xlabel("Model Year", fontsize=11)
    ax2.set_ylabel("Average Records / Vehicle", fontsize=11)
    ax2.grid(True, linestyle=":", alpha=0.7)

    # Adjust X-axis ticks for the bottom plot
    if years:
        ax2.set_xticks(range(min(years), max(years) + 1, 2))

    plt.tight_layout()

    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / "recent_concentration_analysis.png"
    plt.savefig(file_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Investigative chart successfully saved: {file_path}")


def run_eda(df: pl.DataFrame, output_dir: Path) -> None:
    """
    Executes the active exploratory data analysis (EDA) routines and saves the charts.

    This wrapper function calls the necessary plotting and analysis routines to explore
    unique vehicle counts, temporal data distribution, and vehicle age frequencies.
    #"""
    # analyze_unique_vehicles_by_brand_and_fuel(df)
    # plot_vehicle_age_distribution(df, output_dir)
    # plot_temporal_distribution(df, output_dir)
    # analyze_recent_concentration(df, output_dir)
    # check_multiple_t0_records(df)
    plot_depreciation_curves(df, output_dir)
    plot_yoy_depreciation_by_calendar_year(df, output_dir)
    # analyze_price_brackets(df, output_dir)
    run_segmented_price_analysis(df, output_dir)


def check_multiple_t0_records(df: pl.DataFrame) -> None:
    """
    Verifies and prints full records of vehicle cohorts that have multiple entries
    when their age is 0.
    """
    print("\n--- Investigating Multiple Records at Age 0 (t=0) ---")

    cohort_keys = ["codigo_fipe", "ano_modelo", "sigla_combustivel"]

    # 1. Filtra apenas os registros no ano de lançamento (idade_anos == 0)
    df_zeros = df.filter(pl.col("idade_anos") == 0)

    # 2. Conta a quantidade de registros para cada carro único nesse ano
    df_counts = df_zeros.group_by(cohort_keys).len(name="t0_records_count")

    # 3. Filtra apenas os carros que apareceram mais de uma vez com idade 0
    df_multiple = df_counts.filter(pl.col("t0_records_count") > 1)

    num_cohorts_with_repetition = df_multiple.height
    print(
        f"Total de veículos únicos com repetições no ano zero: {num_cohorts_with_repetition:,}"
    )

    if num_cohorts_with_repetition == 0:
        print("Nenhum veículo possui repetição no ano zero.")
        return

    # 4. Junta com a base para recuperar todas as colunas originais desses carros repetidos
    df_full_multiple = df_zeros.join(df_multiple, on=cohort_keys, how="inner").sort(
        cohort_keys + ["data_referencia"]
    )

    # 5. Pega os primeiros 3 carros diferentes para imprimir as linhas completas
    # (limitado a 3 para não travar o seu terminal com milhares de prints)
    unique_multiple_cohorts = df_multiple.head(3).to_dicts()

    print("\nImprimindo TODAS as linhas e colunas para 3 exemplos:")
    for cohort in unique_multiple_cohorts:
        print(
            f"\n>> FIPE: {cohort['codigo_fipe']} | Ano: {cohort['ano_modelo']} | Combustível: '{cohort['sigla_combustivel']}' | Total de Registros: {cohort['t0_records_count']}"
        )

        cohort_rows = df_full_multiple.filter(
            (pl.col("codigo_fipe") == cohort["codigo_fipe"])
            & (pl.col("ano_modelo") == cohort["ano_modelo"])
            & (pl.col("sigla_combustivel") == cohort["sigla_combustivel"])
        )

        # Força o Polars a não esconder nenhuma coluna (tbl_cols=-1) nem linha (tbl_rows=-1)
        with pl.Config(tbl_rows=-1, tbl_cols=-1):
            print(cohort_rows)


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


def plot_depreciation_curves(
    df: pl.DataFrame,
    output_dir: Path,
    title_suffix: str = "",
    filename_suffix: str = "",
) -> None:
    """
    Plots the high-resolution average depreciation curves by age in months.
    """
    df_curves = (
        df.group_by(["idade_meses", "sigla_combustivel"])
        .agg(pl.col("taxa_retencao").mean().alias("media_retencao"))
        .sort("idade_meses")
    )

    pivot_df = df_curves.pivot(
        values="media_retencao", index="idade_meses", on="sigla_combustivel"
    ).sort("idade_meses")

    print("\n--- Average Value Retention by Age (Months) and Fuel Type ---")
    with pl.Config(tbl_rows=20):
        print(pivot_df.head(20))

    ages_months = pivot_df["idade_meses"].to_list()

    styles = {
        "g": ("Gasoline", "#1f77b4", "-"),
        "d": ("Diesel", "#ff7f0e", "-"),
        "f": ("Flex", "#2ca02c", "-"),
        "h": ("Hybrid", "#17becf", "-"),
        "l": ("Electric", "#d62728", "-"),
    }

    fig, ax = plt.subplots(figsize=(10, 6))

    for acronym, (label, color, linestyle) in styles.items():
        if acronym in pivot_df.columns:
            values = [
                (v * 100) if v is not None else None
                for v in pivot_df[acronym].to_list()
            ]
            linewidth = 2.5 if acronym in ["l", "h"] else 1.5

            # Sem marcadores ("o") para não poluir visualmente a linha densa de 240 meses
            ax.plot(
                ages_months,
                values,
                label=label,
                color=color,
                linestyle=linestyle,
                linewidth=linewidth,
            )

    ax.set_title(
        f"Average Vehicle Depreciation Curves by Fuel Type{title_suffix}",
        fontsize=13,
        fontweight="bold",
    )
    ax.set_xlabel("Vehicle Age (Months)", fontsize=11)
    ax.set_ylabel("Value Retention Rate (%)", fontsize=11)

    ax.set_ylim(bottom=0, top=150)

    # Eixo X configurado para apresentar marcadores de 24 em 24 meses (2 anos)
    if ages_months:
        ax.set_xticks(range(0, max(ages_months) + 1, 24))

    ax.grid(True, linestyle=":", alpha=0.7)
    ax.legend(title="Fuel Type", loc="upper right")

    plt.tight_layout()
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"depreciation_curves_monthly{filename_suffix}.png"
    plt.savefig(file_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"High-resolution depreciation curves chart successfully saved: {file_path}")


def plot_yoy_depreciation_by_calendar_year(
    df: pl.DataFrame,
    output_dir: Path,
    title_suffix: str = "",
    filename_suffix: str = "",
) -> None:
    """
    Calculates and plots the Year-over-Year (YoY) average price change
    by calendar year and fuel type to analyze macroeconomic market trends.
    Positive values represent appreciation, negative values represent depreciation.
    """
    print("\n--- Calculating YoY Price Change by Calendar Year ---")

    # 1. Extrair o ano do calendário da cotação
    df_yearly = df.with_columns(
        pl.col("data_referencia").dt.year().alias("ano_calendario")
    )

    # 2. Obter o preço médio de cada carro específico (FIPE + Ano Modelo) em cada ano calendário
    cohort_keys = ["codigo_fipe", "ano_modelo", "sigla_combustivel"]

    df_car_yearly = (
        df_yearly.group_by(cohort_keys + ["ano_calendario"])
        .agg(pl.col("valor_centavos").mean().alias("preco_medio_ano"))
        .sort(cohort_keys + ["ano_calendario"])
    )

    # 3. Deslocar (shift) para obter o preço do MESMO carro no ano ANTERIOR
    df_car_yearly = df_car_yearly.with_columns(
        pl.col("preco_medio_ano").shift(1).over(cohort_keys).alias("preco_ano_anterior")
    )

    # 4. Calcular a Variação YoY: (Preço Atual - Preço Anterior) / Preço Anterior
    # Valores POSITIVOS = Valorização (Appreciation)
    # Valores NEGATIVOS = Desvalorização (Depreciation)
    df_car_yearly = df_car_yearly.with_columns(
        (
            (
                (pl.col("preco_medio_ano") - pl.col("preco_ano_anterior"))
                / pl.col("preco_ano_anterior")
            )
            * 100
        ).alias("variacao_yoy_pct")
    )

    # 5. Agrupar por Ano Calendário e Combustível para tirar a média do mercado
    df_market_yearly = (
        df_car_yearly.drop_nulls("variacao_yoy_pct")
        .group_by(["ano_calendario", "sigla_combustivel"])
        .agg(pl.col("variacao_yoy_pct").mean().alias("media_variacao_anual"))
        .sort("ano_calendario")
    )

    # 6. Pivotar para o gráfico
    pivot_df = df_market_yearly.pivot(
        values="media_variacao_anual", index="ano_calendario", on="sigla_combustivel"
    ).sort("ano_calendario")

    print("\n--- YoY Average Price Change (%) by Calendar Year ---")
    with pl.Config(tbl_rows=20):
        print(pivot_df)

    years = pivot_df["ano_calendario"].to_list()

    styles = {
        "g": ("Gasoline", "#1f77b4", "-"),
        "d": ("Diesel", "#ff7f0e", "-"),
        "f": ("Flex", "#2ca02c", "-"),
        "h": ("Hybrid", "#17becf", "-"),
        "l": ("Electric", "#d62728", "-"),
    }

    fig, ax = plt.subplots(figsize=(10, 6))

    for acronym, (label, color, linestyle) in styles.items():
        if acronym in pivot_df.columns:
            values = pivot_df[acronym].to_list()
            linewidth = 2.5 if acronym in ["l", "h"] else 1.5

            ax.plot(
                years,
                values,
                label=label,
                color=color,
                linestyle=linestyle,
                linewidth=linewidth,
                marker="s",
                markersize=5,
            )

    ax.set_title(
        f"Macroeconomic Trend: YoY Average Price Change{title_suffix}",
        fontsize=13,
        fontweight="bold",
    )
    ax.set_xlabel("Calendar Year", fontsize=11)
    ax.set_ylabel(
        "Average YoY Price Change (%)", fontsize=11
    )  # Atualizado para refletir a nova lógica

    # Linha zero e textos reposicionados
    ax.axhline(0, color="black", linewidth=1.2, linestyle="--")

    if years:
        # Posição X deslocada ligeiramente para a direita (1 ano à frente do mínimo)
        x_text_pos = min(years) + 1

        # Textos colados à linha (offset de 0.5% a 1% dependendo da escala, ajustável se necessário)
        ax.text(
            x_text_pos,
            0.5,
            " Appreciation",
            color="gray",
            verticalalignment="bottom",
            fontweight="bold",
            fontsize=10,
        )
        ax.text(
            x_text_pos,
            -0.5,
            " Depreciation",
            color="gray",
            verticalalignment="top",
            fontweight="bold",
            fontsize=10,
        )

        ax.set_xticks(range(min(years), max(years) + 1, 2))

    ax.grid(True, linestyle=":", alpha=0.7)
    ax.legend(title="Fuel Type", loc="best")

    plt.tight_layout()
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"macro_depreciation_yoy{filename_suffix}.png"
    plt.savefig(file_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Macroeconomic YoY price change chart successfully saved: {file_path}")


def analyze_price_brackets(df: pl.DataFrame, output_dir: Path) -> None:
    """
    Analyzes the distribution of launch prices by fuel type to identify
    the optimal price brackets for empirical matching.
    Focuses on vehicles launched from 2018 onwards to ensure fair technological comparison.
    """
    print("\n--- Analyzing Launch Price Brackets (>= 2018) ---")

    # # 0. Printar analise de quantos veiculos eletricos tem por ano de lancamento
    # electric_vehicles_df = (
    #     df.filter(pl.col("sigla_combustivel").is_in(["l"]))
    #     .group_by("ano_lancamento")
    #     .len()
    #     .sort("ano_lancamento")
    # )

    # print("\n--- Electric Vehicles Count by Launch Year ---")
    # with pl.Config(tbl_rows=-1):
    #     print(electric_vehicles_df)

    # hybrid_vehicles_df = (
    #     df.filter(pl.col("sigla_combustivel").is_in(["h"]))
    #     .group_by("ano_lancamento")
    #     .len()
    #     .sort("ano_lancamento")
    # )

    # print("\n--- Hybrid Vehicles Count by Launch Year ---")
    # with pl.Config(tbl_rows=-1):
    #     print(hybrid_vehicles_df)

    # 1. Isolar os veículos únicos e converter centavos para Reais
    df_prices = (
        df.filter(pl.col("ano_lancamento") >= 2019)
        .select(["codigo_fipe", "ano_modelo", "sigla_combustivel", "preco_lancamento"])
        .unique()
        .with_columns((pl.col("preco_lancamento") / 100).alias("preco_reais"))
    )

    # 2. Calcular estatísticas descritivas (Quartis) para o terminal
    stats_df = (
        df_prices.group_by("sigla_combustivel")
        .agg(
            [
                pl.len().alias("qtd_veiculos"),
                pl.col("preco_reais").quantile(0.25).alias("q1_25%"),
                pl.col("preco_reais").median().alias("mediana_50%"),
                pl.col("preco_reais").quantile(0.75).alias("q3_75%"),
                pl.col("preco_reais").max().alias("maximo"),
            ]
        )
        .sort("mediana_50%")
    )

    print("\nFaixas de Preço de Lançamento (Em R$):")
    with pl.Config(tbl_rows=-1):
        print(stats_df)

    # 3. Gerar o Boxplot Comparativo
    # Preparar dados em listas separadas para o Matplotlib
    data_to_plot = []
    labels = []
    colors = []

    styles = {
        "f": ("Flex", "#2ca02c"),
        "g": ("Gasoline", "#1f77b4"),
        "d": ("Diesel", "#ff7f0e"),
        "h": ("Hybrid", "#17becf"),
        "l": ("Electric", "#d62728"),
    }

    # Ordenar pela mediana para o gráfico ficar progressivo
    order = stats_df["sigla_combustivel"].to_list()

    for acronym in order:
        if acronym in styles:
            label, color = styles[acronym]
            prices = df_prices.filter(pl.col("sigla_combustivel") == acronym)[
                "preco_reais"
            ].to_list()
            data_to_plot.append(prices)
            labels.append(label)
            colors.append(color)

    fig, ax = plt.subplots(figsize=(10, 6))

    bplot = ax.boxplot(
        data_to_plot,
        patch_artist=True,
        tick_labels=labels,
        showfliers=False,  # Oculta outliers extremos (ex: carros de 5 milhões) para focar no mercado real
    )

    # Colorir as caixas
    for patch, color in zip(bplot["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    for median in bplot["medians"]:
        median.set(color="black", linewidth=2)

    # ax.set_title(
    #     "Launch Price Distribution by Fuel Type (Cohorts >= 2018)",
    #     fontsize=13,
    #     fontweight="bold",
    # )
    ax.set_ylabel("Launch Price (R$)", fontsize=11)
    ax.grid(axis="y", linestyle=":", alpha=0.7)

    # Formatar o eixo Y para não usar notação científica
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: f"{x:,.0f}"))

    plt.tight_layout()
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / "launch_price_brackets.png"
    plt.savefig(file_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Price brackets boxplot successfully saved: {file_path}")


def run_segmented_price_analysis(df: pl.DataFrame, output_dir: Path) -> None:
    """
    Segments the post-2018 cohort into Entry, Mid-range, and Luxury brackets
    based on global market launch prices, then runs the depreciation plots
    for each segment to ensure fair empirical matching.
    """
    print("\n--- Segmenting Cohort (>= 2019) by Global Launch Price ---")

    # 1. Filtra a coorte de interesse (como decidido pela sua análise)
    df_recent = df.filter(pl.col("ano_lancamento") >= 2019)

    # 2. Encontra o Q1 e Q3 GLOBAIS isolando cada veículo único
    # (para não dar peso extra a carros que ficaram mais meses na tabela)
    df_prices = df_recent.select(
        ["codigo_fipe", "ano_modelo", "sigla_combustivel", "preco_lancamento"]
    ).unique()

    q1 = df_prices["preco_lancamento"].quantile(0.25)
    q3 = df_prices["preco_lancamento"].quantile(0.75)

    print(f"Limiar Global Q1 (Fim da linha de Entrada): R$ {q1 / 100:,.2f}")
    print(f"Limiar Global Q3 (Início da linha de Luxo): R$ {q3 / 100:,.2f}")

    # 3. Rotula o dataframe principal com as faixas de preço
    df_segmented = df_recent.with_columns(
        pl.when(pl.col("preco_lancamento") <= q1)
        .then(pl.lit("Entrada"))
        .when(pl.col("preco_lancamento") <= q3)
        .then(pl.lit("Intermediario"))
        .otherwise(pl.lit("Luxo"))
        .alias("segmento_preco")
    )

    # 4. Itera sobre cada segmento gerando os gráficos de comparação justa
    segments = ["Entrada", "Intermediario", "Luxo"]

    for seg in segments:
        print(f"\n>> Processando Segmento: {seg} <<")
        df_seg = df_segmented.filter(pl.col("segmento_preco") == seg)

        if df_seg.height == 0:
            print(f"Nenhum registro encontrado no segmento {seg}.")
            continue

        # Imprime quais matrizes energéticas efetivamente existem neste segmento
        counts = df_seg.select(
            ["codigo_fipe", "ano_modelo", "sigla_combustivel"]
        ).unique()
        with pl.Config(tbl_rows=-1):
            print(counts.group_by("sigla_combustivel").len())

        # Cria uma sub-pasta para não desorganizar o seu diretório de output
        seg_dir = output_dir / seg
        seg_dir.mkdir(parents=True, exist_ok=True)

        # Chama as funções passando os sufixos para identificar visualmente a categoria
        plot_depreciation_curves(
            df_seg,
            output_dir=seg_dir,
            title_suffix=f" - Segmento: {seg}",
            filename_suffix=f"_{seg.lower()}",
        )

        plot_yoy_depreciation_by_calendar_year(
            df_seg,
            output_dir=seg_dir,
            title_suffix=f" - Segmento: {seg}",
            filename_suffix=f"_{seg.lower()}",
        )


# ==========================================
# MAIN
# ==========================================


def main():
    """
    Main execution flow integrating data loading, preprocessing, and exploratory analysis.

    This function defines the pipeline by loading the raw parquet file, orchestrating
    cleaning and preprocessing steps, presenting a final overview of the transformed
    dataset, and running the exploratory data analysis suite.
    """
    input_file = ASSETS_DIR / "fipex-prices-latest-merged.parquet"

    print("Loading data...")
    df = pl.read_parquet(input_file)
    # view_dataframe(df)

    df = clean_data(df)
    df = preprocess_data(df)
    df = calculate_value_retention(df)
    # view_dataframe(df)
    run_eda(df, OUTPUT_DIR)


if __name__ == "__main__":
    main()
