"""
Activity 3: encoding of vehicle value-retention series as 2D images.

For each minimum length T in `windows` (24, 32, 48, 64 months), every vehicle launched
from `min_launch_year` onwards that has at least T months of history is represented by
the series of its first T months (idade_meses = 0 .. T-1) of Value Retention Rate (VRR).
Each series is encoded as three T x T images, with no PAA and no resizing (S = T):

- GASF: Gramian Angular Summation Field
- GADF: Gramian Angular Difference Field
- MTF:  Markov Transition Field

Reference: Wang & Oates, "Imaging Time-Series to Improve Classification and Imputation".
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from preprocess import FUEL_TYPES_MAP

COHORT_KEYS = ["codigo_fipe", "ano_modelo", "sigla_combustivel"]


# ==========================================
# SERIES PREPARATION
# ==========================================


def compute_price_thresholds(
    df: pl.DataFrame, min_launch_year: int = 2019
) -> tuple[float, float]:
    """
    Computes the global Q1 and Q3 of launch prices (in R$) used to segment vehicles
    into Entrada / Intermediario / Luxo.

    Follows the same procedure as `run_segmented_price_analysis` in eda.py: the
    quartiles are taken over all unique vehicles launched from 'min_launch_year',
    regardless of how long their history is.
    """
    prices = (
        df.filter(pl.col("ano_lancamento") >= min_launch_year)
        .select(COHORT_KEYS + ["preco_lancamento"])
        .unique()
        .with_columns((pl.col("preco_lancamento") / 100).alias("preco_reais"))
    )
    q1_reais = prices["preco_reais"].quantile(0.25)
    q3_reais = prices["preco_reais"].quantile(0.75)
    return q1_reais, q3_reais


def add_price_segment(
    vehicles: pl.DataFrame, q1_reais: float, q3_reais: float
) -> pl.DataFrame:
    """
    Labels each vehicle with its launch price segment: Entrada (<= Q1),
    Intermediario (Q1 < x <= Q3) or Luxo (> Q3).
    """
    price_reais = pl.col("preco_lancamento") / 100
    return vehicles.with_columns(
        pl.when(price_reais <= q1_reais)
        .then(pl.lit("Entrada"))
        .when(price_reais <= q3_reais)
        .then(pl.lit("Intermediario"))
        .otherwise(pl.lit("Luxo"))
        .alias("segmento_preco")
    )


def build_series_matrix(
    df: pl.DataFrame,
    window: int,
    min_launch_year: int = 2019,
    max_gap_frac: float = 0.10,
) -> tuple[pl.DataFrame, np.ndarray]:
    """
    Builds the matrix of VRR series (one row per vehicle) over the first 'window' months.

    A vehicle is kept if it was launched from 'min_launch_year' and has history
    covering months 0 .. window-1. Months missing inside the window are filled by
    linear interpolation; vehicles whose fraction of missing months exceeds
    'max_gap_frac' are discarded. If several records exist for the same vehicle and
    month, their mean is used.

    Returns the vehicle metadata (same row order as the matrix) and the matrix of
    VRR values (ratio, not percentage) with shape (n_vehicles, window).
    """
    df_recent = df.filter(pl.col("ano_lancamento") >= min_launch_year)

    vehicles = (
        df_recent.group_by(COHORT_KEYS)
        .agg(
            [
                pl.col("nome_marca").first(),
                pl.col("ano_lancamento").first(),
                pl.col("data_lancamento").first(),
                pl.col("preco_lancamento").first(),
                pl.col("idade_meses").max().alias("max_idade_meses"),
            ]
        )
        .sort(COHORT_KEYS)
    )
    n_all = vehicles.height

    vehicles = vehicles.filter(pl.col("max_idade_meses") >= window - 1).with_row_index(
        "vehicle_id"
    )
    n_long = vehicles.height
    print(
        f"Vehicles launched >= {min_launch_year}: {n_all:,} | "
        f"with at least {window} months of history: {n_long:,}"
    )

    if n_long == 0:
        return vehicles.drop("vehicle_id"), np.empty((0, window))

    window_df = (
        df_recent.filter(pl.col("idade_meses") < window)
        .group_by(COHORT_KEYS + ["idade_meses"])
        .agg(pl.col("taxa_retencao").mean())
        .join(
            vehicles.select(COHORT_KEYS + ["vehicle_id"]),
            on=COHORT_KEYS,
            how="inner",
        )
    )

    matrix = np.full((n_long, window), np.nan, dtype=np.float64)
    matrix[
        window_df["vehicle_id"].to_numpy(), window_df["idade_meses"].to_numpy()
    ] = window_df["taxa_retencao"].to_numpy()

    # Descarta séries com buracos demais dentro da janela
    n_missing = np.isnan(matrix).sum(axis=1)
    keep = (n_missing / window) <= max_gap_frac
    print(
        f"Discarded for gaps > {max_gap_frac:.0%} of the window: {int((~keep).sum()):,} | "
        f"kept with at least one interpolated month: {int(((n_missing > 0) & keep).sum()):,}"
    )

    vehicles = vehicles.filter(pl.Series(keep)).with_columns(
        pl.Series("meses_interpolados", n_missing[keep])
    )
    matrix = matrix[keep]

    # Interpola linearmente os meses faltantes (extremos ficam no último valor válido)
    months = np.arange(window)
    for i in np.flatnonzero(np.isnan(matrix).any(axis=1)):
        valid = ~np.isnan(matrix[i])
        matrix[i] = np.interp(months, months[valid], matrix[i][valid])

    vehicles = vehicles.drop("vehicle_id").with_row_index("idx")
    return vehicles, matrix


def scale_series(
    series: np.ndarray, vrr_max: float = 1.5
) -> tuple[np.ndarray, float]:
    """
    Rescales VRR values to [0, 1] with a fixed global scale (0 .. vrr_max), so the
    absolute level of depreciation is preserved across vehicles (unlike per-series
    min-max). Values outside the range are clipped.

    Returns the scaled matrix and the fraction of values that had to be clipped.
    """
    scaled = series / vrr_max
    clipped_frac = float(((scaled > 1.0) | (scaled < 0.0)).mean())
    return np.clip(scaled, 0.0, 1.0), clipped_frac


# ==========================================
# ENCODINGS
# ==========================================


def gramian_angular_fields(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Computes GASF and GADF for a batch of series already rescaled to [0, 1].

    With phi = arccos(x):
        GASF[i, j] = cos(phi_i + phi_j) = x_i * x_j - sqrt(1 - x_i^2) * sqrt(1 - x_j^2)
        GADF[i, j] = sin(phi_i - phi_j) = sqrt(1 - x_i^2) * x_j - x_i * sqrt(1 - x_j^2)

    Input shape (N, T); output shapes (N, T, T), dtype float32.
    """
    x = np.clip(x, 0.0, 1.0)
    s = np.sqrt(1.0 - x**2)

    gasf = x[:, :, None] * x[:, None, :] - s[:, :, None] * s[:, None, :]
    gadf = s[:, :, None] * x[:, None, :] - x[:, :, None] * s[:, None, :]
    return gasf.astype(np.float32), gadf.astype(np.float32)


def markov_transition_fields(
    x: np.ndarray, n_bins: int = 8, strategy: str = "quantile"
) -> np.ndarray:
    """
    Computes the Markov Transition Field for a batch of series in [0, 1].

    Each series is discretized into 'n_bins' bins, a first-order Markov transition
    matrix W (n_bins x n_bins, rows normalized to sum 1) is estimated from consecutive
    steps, and the field is M[i, j] = W[bin(x_i), bin(x_j)].

    strategy:
        "quantile": bin edges are the quantiles of each series (as in the paper).
        "uniform":  bin edges are fixed and equally spaced over the global [0, 1] scale,
                    which keeps the absolute level information in the MTF.

    Input shape (N, T); output shape (N, T, T), dtype float32.
    """
    n, t = x.shape
    out = np.empty((n, t, t), dtype=np.float32)
    inner_probs = np.linspace(0.0, 1.0, n_bins + 1)[1:-1]

    for k in range(n):
        series = x[k]
        if strategy == "quantile":
            edges = np.quantile(series, inner_probs)
        elif strategy == "uniform":
            edges = inner_probs
        else:
            raise ValueError(f"Unknown MTF strategy: {strategy}")

        bins = np.digitize(series, edges)  # valores em 0 .. n_bins-1

        w = np.zeros((n_bins, n_bins), dtype=np.float64)
        np.add.at(w, (bins[:-1], bins[1:]), 1.0)
        row_sum = w.sum(axis=1, keepdims=True)
        w = np.divide(w, row_sum, out=np.zeros_like(w), where=row_sum > 0)

        out[k] = w[bins[:, None], bins[None, :]]

    return out


# ==========================================
# OUTPUT
# ==========================================


def plot_encoding_examples(
    series: np.ndarray,
    gasf: np.ndarray,
    gadf: np.ndarray,
    mtf: np.ndarray,
    meta: pl.DataFrame,
    window: int,
    file_path: Path,
    seed: int = 42,
) -> None:
    """
    Saves a grid with one random Electric, one Hybrid and one Gasoline vehicle,
    showing the VRR series and its GASF, GADF and MTF images.
    """
    rng = np.random.default_rng(seed)
    fuel_col = meta["sigla_combustivel"].to_numpy()
    fuels = [f for f in ("l", "h", "g") if (fuel_col == f).any()]
    if not fuels:
        return

    fig, axes = plt.subplots(
        len(fuels), 4, figsize=(15, 3.6 * len(fuels)), squeeze=False
    )
    months = np.arange(window)
    panels = [
        (gasf, -1.0, 1.0, "GASF"),
        (gadf, -1.0, 1.0, "GADF"),
        (mtf, 0.0, 1.0, "MTF"),
    ]

    for r, fuel in enumerate(fuels):
        k = int(rng.choice(np.flatnonzero(fuel_col == fuel)))
        row = meta.row(k, named=True)

        ax = axes[r, 0]
        ax.plot(months, series[k] * 100, color="black", linewidth=1.8)
        ax.set_ylabel(
            f"{FUEL_TYPES_MAP.get(fuel, fuel)}\nFIPE {row['codigo_fipe']} / {row['ano_modelo']}",
            fontsize=9,
        )
        ax.grid(True, linestyle=":", alpha=0.6)

        for c, (images, vmin, vmax, name) in enumerate(panels, start=1):
            ax_img = axes[r, c]
            ax_img.imshow(images[k], cmap="rainbow", vmin=vmin, vmax=vmax)
            ax_img.set_xticks([])
            ax_img.set_yticks([])
            if r == 0:
                ax_img.set_title(name, fontsize=11, fontweight="bold")

    axes[0, 0].set_title("VRR (%)", fontsize=11, fontweight="bold")
    axes[-1, 0].set_xlabel("Vehicle Age (Months)", fontsize=10)

    plt.tight_layout()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(file_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Examples grid successfully saved: {file_path}")


def run_encoding(
    df: pl.DataFrame,
    output_dir: Path,
    windows: tuple = (24, 32, 48, 64),
    min_launch_year: int = 2019,
    vrr_max: float = 1.5,
    n_bins: int = 8,
    mtf_strategy: str = "quantile",
    max_gap_frac: float = 0.10,
) -> None:
    """
    Generates the GASF, GADF and MTF representations for each minimum length in 'windows'.

    For each window T, a folder 'window_TT' is created inside 'output_dir' with:
        gasf.npy, gadf.npy, mtf.npy  float32 arrays of shape (N, T, T)
        series_vrr.npy                float32 array (N, T) with the raw VRR series (ratio),
                                      to be used by the Euclidean / DTW baselines
        metadata.parquet              one row per vehicle, same order as the arrays
        config.json                   parameters used to generate the files
        examples.png                  grid with example vehicles and their images
    """
    print(f"\n--- Encoding series as images (launch year >= {min_launch_year}) ---")

    q1_reais, q3_reais = compute_price_thresholds(df, min_launch_year)
    print(f"Q1 (end of Entrada): R$ {q1_reais:,.2f} | Q3 (start of Luxo): R$ {q3_reais:,.2f}")

    for window in windows:
        print(f"\n>> Window: {window} months <<")
        vehicles, series = build_series_matrix(
            df, window, min_launch_year=min_launch_year, max_gap_frac=max_gap_frac
        )

        if vehicles.height == 0:
            print("No vehicles available for this window, skipping.")
            continue

        scaled, clipped_frac = scale_series(series, vrr_max)
        print(
            f"Values clipped to the [0, {vrr_max:.2f}] VRR scale: {clipped_frac:.3%}"
        )

        gasf, gadf = gramian_angular_fields(scaled)
        mtf = markov_transition_fields(scaled, n_bins=n_bins, strategy=mtf_strategy)

        vehicles = add_price_segment(vehicles, q1_reais, q3_reais)

        print("Unique vehicles by fuel type and price segment:")
        by_segment = (
            vehicles.group_by(["sigla_combustivel", "segmento_preco"])
            .len()
            .pivot(on="segmento_preco", index="sigla_combustivel", values="len")
            .fill_null(0)
            .sort("sigla_combustivel")
        )
        with pl.Config(tbl_rows=-1, tbl_cols=-1):
            print(by_segment)

        window_dir = output_dir / f"window_{window:02d}"
        window_dir.mkdir(parents=True, exist_ok=True)

        np.save(window_dir / "gasf.npy", gasf)
        np.save(window_dir / "gadf.npy", gadf)
        np.save(window_dir / "mtf.npy", mtf)
        np.save(window_dir / "series_vrr.npy", series.astype(np.float32))
        vehicles.write_parquet(window_dir / "metadata.parquet")

        config = {
            "window_months": window,
            "image_size": window,
            "n_vehicles": vehicles.height,
            "min_launch_year": min_launch_year,
            "vrr_scale_max": vrr_max,
            "clipped_fraction": clipped_frac,
            "mtf_bins": n_bins,
            "mtf_strategy": mtf_strategy,
            "max_gap_frac": max_gap_frac,
            "q1_reais": q1_reais,
            "q3_reais": q3_reais,
        }
        with open(window_dir / "config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        plot_encoding_examples(
            series, gasf, gadf, mtf, vehicles, window, window_dir / "examples.png"
        )

        print(
            f"Saved {vehicles.height:,} vehicles to {window_dir} "
            f"(arrays of shape {gasf.shape})"
        )
