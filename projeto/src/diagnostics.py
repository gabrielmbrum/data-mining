"""
Diagnostics for series whose VRR does not start at 100%.

VRR(t=0) = valor_centavos / preco_lancamento, where preco_lancamento is the price of ONE
record at idade_meses == 0. So a series only starts below/above 100% when the same vehicle
(codigo_fipe, ano_modelo, sigla_combustivel) has MORE THAN ONE record in month 0 (the encoding
averages them). This module finds those cases and shows what differs between the duplicates.

Note: the old `check_multiple_t0_records` filters `idade_anos == 0`, i.e. the whole launch
calendar year, so almost every vehicle shows up there. The right filter is `idade_meses == 0`.
"""

import polars as pl

COHORT_KEYS = ["codigo_fipe", "ano_modelo", "sigla_combustivel"]

# Colunas derivadas do preço ou da data: variam naturalmente e não ajudam a achar a causa
DERIVED_COLS = [
    "idade_meses",
    "idade_anos",
    "ano_lancamento",
    "data_lancamento",
    "preco_lancamento",
    "taxa_retencao",
]


def diagnose_t0_duplicates(
    df: pl.DataFrame, min_model_year: int = 2019, n_examples: int = 3
) -> pl.DataFrame:
    """
    Finds vehicles with more than one record in the same month (focusing on month 0)
    and reports what differs between the duplicated records.

    Prints:
      1. how many vehicle-months are duplicated, at month 0 and in later months;
      2. which columns vary inside the duplicated groups (e.g. zero_km, nome_modelo, price);
      3. how far apart the duplicated prices are;
      4. how many series start at a VRR different from 100% and by how much, per fuel type;
      5. a few full examples.

    Returns the duplicated records at month 0 (all columns), sorted by vehicle.
    """
    print(f"\n--- Duplicated records in the same month (model year >= {min_model_year}) ---")

    month_keys = COHORT_KEYS + ["data_referencia"]
    recent = df.filter(pl.col("ano_modelo") >= min_model_year)

    groups = recent.group_by(month_keys).agg(
        [
            pl.len().alias("n_rows"),
            pl.col("idade_meses").first().alias("idade_meses"),
            pl.col("valor_centavos").min().alias("preco_min"),
            pl.col("valor_centavos").max().alias("preco_max"),
        ]
    )
    dup_groups = groups.filter(pl.col("n_rows") > 1)
    dup_t0 = dup_groups.filter(pl.col("idade_meses") == 0)

    n_cohorts = recent.select(COHORT_KEYS).unique().height
    n_cohorts_t0 = dup_t0.select(COHORT_KEYS).unique().height
    print(f"Unique vehicles: {n_cohorts:,}")
    print(f"Vehicle-months with more than one record: {dup_groups.height:,} of {groups.height:,}")
    print(
        f"  at month 0: {dup_t0.height:,} "
        f"({n_cohorts_t0:,} vehicles = {n_cohorts_t0 / n_cohorts:.1%})"
    )
    print(f"  at later months: {dup_groups.filter(pl.col('idade_meses') > 0).height:,}")

    if dup_t0.height == 0:
        print("No duplicated records at month 0.")
        return recent.clear()

    dup_rows = recent.join(dup_t0.select(month_keys), on=month_keys, how="inner").sort(
        month_keys
    )

    # Quais colunas diferem dentro dos grupos duplicados?
    check_cols = [
        c for c in df.columns if c not in month_keys and c not in DERIVED_COLS
    ]
    varying = dup_rows.group_by(month_keys).agg(
        [pl.col(c).n_unique().alias(c) for c in check_cols]
    )
    n_groups = varying.height
    print("\nColumns that differ inside the duplicated groups (month 0):")
    for c in check_cols:
        n_diff = int((varying[c] > 1).sum())
        print(f"  {c:<22} differs in {n_diff:>7,} of {n_groups:,} groups ({n_diff / n_groups:.1%})")

    if "zero_km" in dup_rows.columns:
        mix = dup_rows.group_by(month_keys).agg(
            [
                pl.col("zero_km").any().alias("has_zero_km"),
                (~pl.col("zero_km")).any().alias("has_regular"),
            ]
        )
        both = int((mix["has_zero_km"] & mix["has_regular"]).sum())
        print(
            f"\nGroups mixing a zero_km record with a regular record: {both:,} of {n_groups:,}"
        )
    else:
        print(
            "\n(zero_km column not available: remove 'zero_km' from the drop list in "
            "preprocess_data to check whether duplicates are zero_km vs. regular quotes)"
        )

    # Distância entre os preços duplicados
    spread = dup_t0.with_columns(
        ((pl.col("preco_max") / pl.col("preco_min") - 1) * 100).alias("diferenca_pct")
    )
    print("\nPrice gap between duplicated records (max / min - 1, %):")
    with pl.Config(tbl_cols=-1):
        print(spread["diferenca_pct"].describe())

    # Efeito no VRR do mês 0
    t0 = (
        recent.filter(pl.col("idade_meses") == 0)
        .group_by(COHORT_KEYS)
        .agg(
            [
                pl.len().alias("n_t0"),
                pl.col("taxa_retencao").mean().alias("vrr_t0"),
            ]
        )
    )
    off = t0.filter((pl.col("vrr_t0") - 1).abs() > 1e-9)
    print(
        f"\nVehicles whose VRR at month 0 is not 100%: {off.height:,} of {t0.height:,} "
        f"({off.height / t0.height:.1%})"
    )
    with pl.Config(tbl_cols=-1):
        print((off["vrr_t0"] * 100).describe())

    by_fuel = (
        t0.group_by("sigla_combustivel")
        .agg(
            [
                pl.len().alias("vehicles"),
                ((pl.col("vrr_t0") - 1).abs() > 1e-9).sum().alias("start_not_100"),
            ]
        )
        .with_columns(
            (pl.col("start_not_100") / pl.col("vehicles") * 100).round(1).alias("pct")
        )
        .sort("sigla_combustivel")
    )
    print("\nBy fuel type:")
    with pl.Config(tbl_rows=-1):
        print(by_fuel)

    print(f"\nExamples (all columns) of {n_examples} duplicated vehicles at month 0:")
    for row in dup_t0.sort("n_rows", descending=True).head(n_examples).to_dicts():
        sub = dup_rows.filter(
            pl.all_horizontal([pl.col(k) == row[k] for k in month_keys])
        )
        print(f"\n>> {[row[k] for k in month_keys]} ({row['n_rows']} records)")
        with pl.Config(tbl_rows=-1, tbl_cols=-1, fmt_str_lengths=40):
            print(sub)

    return dup_rows


def diagnose_zero_km_streams(
    df: pl.DataFrame,
    min_model_year: int = 2019,
    max_age: int = 24,
    ages_to_show: tuple = (0, 1, 2, 3, 6, 9, 12, 18, 23),
) -> pl.DataFrame:
    """
    Maps how the zero_km and the regular (model-year) price streams coexist for each vehicle.

    For every vehicle-month in the first 'max_age' months it classifies the month as
    'only_zero_km', 'only_regular' or 'both', and prints:
      1. the share of each class by vehicle age (when does the zero_km stream end?);
      2. the class at month 0 by fuel type;
      3. the distribution of the last month in which a zero_km quote exists;
      4. the median price premium of zero_km over regular when both exist, by age.

    Needs the 'zero_km' column (kept by preprocess_data). Returns the vehicle-month table.
    """
    print(f"\n--- zero_km vs. regular price streams (model year >= {min_model_year}) ---")

    recent_all = df.filter(pl.col("ano_modelo") >= min_model_year)
    recent = recent_all.filter(pl.col("idade_meses") < max_age)

    cm = (
        recent.group_by(COHORT_KEYS + ["idade_meses"])
        .agg(
            [
                pl.col("zero_km").any().alias("has_zero_km"),
                (~pl.col("zero_km")).any().alias("has_regular"),
                pl.col("valor_centavos").filter(pl.col("zero_km")).mean().alias("p_zero_km"),
                pl.col("valor_centavos").filter(~pl.col("zero_km")).mean().alias("p_regular"),
            ]
        )
        .with_columns(
            pl.when(pl.col("has_zero_km") & pl.col("has_regular"))
            .then(pl.lit("both"))
            .when(pl.col("has_zero_km"))
            .then(pl.lit("only_zero_km"))
            .otherwise(pl.lit("only_regular"))
            .alias("stream")
        )
    )

    classes = ["only_zero_km", "only_regular", "both"]

    def pivot_counts(frame: pl.DataFrame, index: str) -> pl.DataFrame:
        out = (
            frame.group_by([index, "stream"])
            .len()
            .pivot(on="stream", index=index, values="len")
            .fill_null(0)
        )
        for c in classes:
            if c not in out.columns:
                out = out.with_columns(pl.lit(0).cast(pl.UInt32).alias(c))
        return (
            out.select([index] + classes)
            .with_columns(pl.sum_horizontal(classes).alias("total"))
            .sort(index)
        )

    by_age = pivot_counts(cm, "idade_meses")
    by_age = by_age.with_columns(
        [(pl.col(c) / pl.col("total") * 100).round(1).alias(f"{c}_%") for c in classes]
    ).filter(pl.col("idade_meses").is_in(list(ages_to_show)))
    print("\nVehicle-months by stream class and age (counts and %):")
    with pl.Config(tbl_rows=-1, tbl_cols=-1):
        print(by_age)

    print("\nStream class at month 0, by fuel type:")
    with pl.Config(tbl_rows=-1, tbl_cols=-1):
        print(pivot_counts(cm.filter(pl.col("idade_meses") == 0), "sigla_combustivel"))

    last_zero_km = (
        recent_all.filter(pl.col("zero_km"))
        .group_by(COHORT_KEYS)
        .agg(pl.col("idade_meses").max().alias("ultimo_mes_zero_km"))
    )
    print(
        f"\nVehicles with at least one zero_km quote: {last_zero_km.height:,} "
        f"of {recent_all.select(COHORT_KEYS).unique().height:,}"
    )
    print("Last month (age) with a zero_km quote:")
    with pl.Config(tbl_cols=-1):
        print(last_zero_km["ultimo_mes_zero_km"].describe())

    premium = (
        cm.filter(pl.col("stream") == "both")
        .with_columns(((pl.col("p_zero_km") / pl.col("p_regular") - 1) * 100).alias("premio_pct"))
        .group_by("idade_meses")
        .agg(
            [
                pl.len().alias("n"),
                pl.col("premio_pct").median().round(2).alias("mediana_premio_%"),
            ]
        )
        .sort("idade_meses")
        .filter(pl.col("idade_meses").is_in(list(ages_to_show)))
    )
    print("\nzero_km premium over the regular quote when both exist (median, %):")
    with pl.Config(tbl_rows=-1):
        print(premium)

    return cm


def diagnose_model_year_vs_launch(
    df: pl.DataFrame, min_launch_year: int = 2019, n_examples: int = 5
) -> pl.DataFrame:
    """
    Compares 'ano_modelo' with 'ano_lancamento' (year of the first quote of the vehicle).

    diff = ano_lancamento - ano_modelo
      diff < 0: the model year was first quoted in the calendar year BEFORE ano_modelo
                (e.g. model year 2024 first quoted in 2023);
      diff = 0: first quote in the same calendar year as the model year;
      diff > 0: the model year is OLDER than the first quote (late listing, so idade_meses = 0
                is not a real launch).

    Prints:
      1. the distribution of diff for the vehicles currently kept (ano_lancamento >= min_launch_year),
         crossed with the stream class at month 0 (only_zero_km / only_regular / both);
      2. how the cohort changes if the cutoff used ano_modelo instead of ano_lancamento;
      3. examples of vehicles whose model year is much older than the first quote.

    Returns one row per vehicle with the diff and the stream class.
    """
    print(f"\n--- ano_modelo vs. ano_lancamento (cutoff {min_launch_year}) ---")

    veh = (
        df.filter(pl.col("idade_meses") == 0)
        .group_by(COHORT_KEYS)
        .agg(
            [
                pl.col("nome_modelo").first(),
                pl.col("ano_lancamento").first(),
                pl.col("data_lancamento").first(),
                pl.col("zero_km").any().alias("has_zero_km"),
                (~pl.col("zero_km")).any().alias("has_regular"),
            ]
        )
        .with_columns(
            [
                (pl.col("ano_lancamento") - pl.col("ano_modelo")).alias("diff"),
                pl.when(pl.col("has_zero_km") & pl.col("has_regular"))
                .then(pl.lit("both"))
                .when(pl.col("has_zero_km"))
                .then(pl.lit("only_zero_km"))
                .otherwise(pl.lit("only_regular"))
                .alias("stream"),
            ]
        )
    )

    kept = veh.filter(pl.col("ano_lancamento") >= min_launch_year)
    classes = ["only_zero_km", "only_regular", "both"]
    table = (
        kept.with_columns(pl.col("diff").clip(-2, 3).alias("diff_clip"))
        .group_by(["diff_clip", "stream"])
        .len()
        .pivot(on="stream", index="diff_clip", values="len")
        .fill_null(0)
    )
    for c in classes:
        if c not in table.columns:
            table = table.with_columns(pl.lit(0).cast(pl.UInt32).alias(c))
    table = (
        table.select(["diff_clip"] + classes)
        .with_columns(pl.sum_horizontal(classes).alias("total"))
        .with_columns((pl.col("total") / kept.height * 100).round(1).alias("total_%"))
        .sort("diff_clip")
    )
    print(
        f"\nVehicles kept today (ano_lancamento >= {min_launch_year}): {kept.height:,}\n"
        "diff = ano_lancamento - ano_modelo (-2 means <= -2, 3 means >= 3), by stream at month 0:"
    )
    with pl.Config(tbl_rows=-1, tbl_cols=-1):
        print(table)

    by_launch = pl.col("ano_lancamento") >= min_launch_year
    by_model = pl.col("ano_modelo") >= min_launch_year
    inclusion = pl.DataFrame(
        {
            "criterion": [
                "both (ano_lancamento and ano_modelo >= cutoff)",
                "only ano_lancamento >= cutoff (older model year, kept today)",
                "only ano_modelo >= cutoff (first quoted before the cutoff, dropped today)",
            ],
            "vehicles": [
                veh.filter(by_launch & by_model).height,
                veh.filter(by_launch & ~by_model).height,
                veh.filter(~by_launch & by_model).height,
            ],
        }
    )
    print("\nEffect of the cutoff criterion:")
    with pl.Config(tbl_rows=-1, tbl_cols=-1, fmt_str_lengths=90):
        print(inclusion)

    print(f"\nExamples of kept vehicles whose model year is >= 2 years older than the first quote:")
    old = kept.filter(pl.col("diff") >= 2).sort("diff", descending=True).head(n_examples)
    with pl.Config(tbl_rows=-1, tbl_cols=-1, fmt_str_lengths=40):
        print(
            old.select(
                ["codigo_fipe", "nome_modelo", "ano_modelo", "data_lancamento", "stream", "diff"]
            )
        )

    return veh
