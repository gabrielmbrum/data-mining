"""
Script to evaluate whether clustering identifies fuel types vs price segments.
Generates quantitative metrics (NMI, ARI, Homogeneity, Completeness, Cramér's V, ANOVA)
and diagnostic plots comparing fuel type vs price bracket influence on clusters.
"""

from pathlib import Path
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import (
    adjusted_rand_score,
    normalized_mutual_info_score,
    homogeneity_score,
    completeness_score,
)
from scipy.stats import chi2_contingency
import statsmodels.api as sm
from statsmodels.formula.api import ols

FUEL_MAP = {
    "l": "Elétrico",
    "h": "Híbrido",
    "g": "Gasolina",
    "f": "Flex",
    "d": "Diesel",
}

FUEL_COLORS = {
    "Elétrico": "#17becf",
    "Híbrido": "#2ca02c",
    "Flex": "#ff7f0e",
    "Gasolina": "#1f77b4",
    "Diesel": "#7f7f7f",
}

SEGMENT_COLORS = {
    "Entrada": "#2ca02c",
    "Intermediario": "#1f77b4",
    "Luxo": "#d62728",
}

def cramers_v(contingency_matrix: np.ndarray) -> float:
    chi2 = chi2_contingency(contingency_matrix)[0]
    n = contingency_matrix.sum()
    if n == 0:
        return 0.0
    phi2 = chi2 / n
    r, k = contingency_matrix.shape
    phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
    rcorr = r - ((r - 1) ** 2) / (n - 1)
    kcorr = k - ((k - 1) ** 2) / (n - 1)
    denom = min((kcorr - 1), (rcorr - 1))
    return np.sqrt(phi2corr / denom) if denom > 0 else 0.0

def run_evaluation():
    base_dir = Path("projeto/output")
    window_dir = base_dir / "encoding" / "window_32"
    clustering_dir = base_dir / "clustering"
    clustering_dir.mkdir(parents=True, exist_ok=True)

    metadata = pl.read_parquet(window_dir / "metadata.parquet")
    series_vrr = np.load(window_dir / "series_vrr.npy")
    n_vehicles, window_len = series_vrr.shape
    months = np.arange(window_len)

    # 1. Fit KMeans K=4 on 1D VRR
    km = KMeans(n_clusters=4, random_state=42, n_init=10).fit(series_vrr)
    labels = km.labels_

    # Map cluster names by their trajectory behavior
    cluster_deltas = []
    for c in range(4):
        c_mean = series_vrr[labels == c].mean(axis=0)
        delta = (c_mean[-1] - c_mean[0]) * 100
        cluster_deltas.append((c, delta))
    # Sort clusters by final delta so names are intuitive:
    # Most depreciated -> Most appreciated
    sorted_clusters = [c for c, _ in sorted(cluster_deltas, key=lambda x: x[1])]
    remap = {orig: f"C{new+1}" for new, orig in enumerate(sorted_clusters)}
    cluster_names = [remap[c] for c in labels]

    meta_df = metadata.with_columns([
        pl.Series("cluster", cluster_names),
        pl.col("sigla_combustivel").replace(FUEL_MAP).alias("nome_combustivel"),
        ((pl.Series(series_vrr[:, -1]) - pl.Series(series_vrr[:, 0])) * 100.0).alias("delta_vrr"),
        (pl.col("preco_lancamento") / 100.0).alias("preco_reais"),
    ])

    pdf = pd.DataFrame(meta_df.to_dict())

    # 2. Compute metrics
    # Contingency matrices
    ct_fuel = pd.crosstab(pdf["cluster"], pdf["nome_combustivel"])
    ct_seg = pd.crosstab(pdf["cluster"], pdf["segmento_preco"])

    metrics = {
        "Combustível": {
            "ARI": adjusted_rand_score(pdf["nome_combustivel"], pdf["cluster"]),
            "NMI": normalized_mutual_info_score(pdf["nome_combustivel"], pdf["cluster"]),
            "Homogeneidade": homogeneity_score(pdf["nome_combustivel"], pdf["cluster"]),
            "Completude": completeness_score(pdf["nome_combustivel"], pdf["cluster"]),
            "Cramer_V": cramers_v(ct_fuel.values),
        },
        "Faixa_Preco": {
            "ARI": adjusted_rand_score(pdf["segmento_preco"], pdf["cluster"]),
            "NMI": normalized_mutual_info_score(pdf["segmento_preco"], pdf["cluster"]),
            "Homogeneidade": homogeneity_score(pdf["segmento_preco"], pdf["cluster"]),
            "Completude": completeness_score(pdf["segmento_preco"], pdf["cluster"]),
            "Cramer_V": cramers_v(ct_seg.values),
        }
    }

    # 3. Two-Way ANOVA
    model_anova = ols("delta_vrr ~ C(nome_combustivel) + C(segmento_preco)", data=pdf).fit()
    anova_table = sm.stats.anova_lm(model_anova, typ=2)

    # 4. Generate Diagnostic Visualization (2x2 Panel)
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))

    # Panel A: Fuel distribution per cluster (relative to total fuel type to show recall/concentration)
    ax_a = axes[0, 0]
    # Rows: fuel types, Columns: clusters
    ct_fuel_pct = pd.crosstab(pdf["nome_combustivel"], pdf["cluster"], normalize="index") * 100.0
    cols_order = sorted(ct_fuel_pct.columns)
    ct_fuel_pct = ct_fuel_pct[cols_order]

    im_a = ax_a.imshow(ct_fuel_pct.values, cmap="YlGnBu", aspect="auto")
    ax_a.set_xticks(range(len(cols_order)))
    ax_a.set_xticklabels(cols_order, fontsize=11, fontweight="bold")
    ax_a.set_yticks(range(len(ct_fuel_pct.index)))
    ax_a.set_yticklabels(ct_fuel_pct.index, fontsize=10)
    ax_a.set_title("A. Concentração por Combustível (% de cada matriz nos Clusters)", fontsize=11, fontweight="bold")
    for i in range(ct_fuel_pct.shape[0]):
        for j in range(ct_fuel_pct.shape[1]):
            val = ct_fuel_pct.values[i, j]
            color = "white" if val > 40 else "black"
            ax_a.text(j, i, f"{val:.1f}%", ha="center", va="center", color=color, fontweight="bold", fontsize=10)
    plt.colorbar(im_a, ax=ax_a, fraction=0.046, pad=0.04)

    # Panel B: Price Segment distribution per cluster (% of segment in each cluster)
    ax_b = axes[0, 1]
    ct_seg_pct = pd.crosstab(pdf["segmento_preco"], pdf["cluster"], normalize="index") * 100.0
    ct_seg_pct = ct_seg_pct[cols_order]
    im_b = ax_b.imshow(ct_seg_pct.values, cmap="YlOrRd", aspect="auto")
    ax_b.set_xticks(range(len(cols_order)))
    ax_b.set_xticklabels(cols_order, fontsize=11, fontweight="bold")
    ax_b.set_yticks(range(len(ct_seg_pct.index)))
    ax_b.set_yticklabels(ct_seg_pct.index, fontsize=10)
    ax_b.set_title("B. Concentração por Faixa de Preço (% de cada faixa nos Clusters)", fontsize=11, fontweight="bold")
    for i in range(ct_seg_pct.shape[0]):
        for j in range(ct_seg_pct.shape[1]):
            val = ct_seg_pct.values[i, j]
            color = "white" if val > 40 else "black"
            ax_b.text(j, i, f"{val:.1f}%", ha="center", va="center", color=color, fontweight="bold", fontsize=10)
    plt.colorbar(im_b, ax=ax_b, fraction=0.046, pad=0.04)

    # Panel C: Average VRR Trajectory by Fuel Type vs Price Segment
    ax_c = axes[1, 0]
    for fuel, f_name in FUEL_MAP.items():
        mask = metadata["sigla_combustivel"] == fuel
        if mask.sum() > 0:
            sub_series = series_vrr[mask.to_numpy()] * 100.0
            mean_c = sub_series.mean(axis=0)
            ax_c.plot(months, mean_c, label=f_name, color=FUEL_COLORS.get(f_name, "black"), linewidth=2.2)
    ax_c.axhline(100.0, color="gray", linestyle="--", alpha=0.7)
    ax_c.set_title("C. Trajetória Média de VRR por Tipo de Combustível", fontsize=11, fontweight="bold")
    ax_c.set_xlabel("Idade do Ativo (Meses)", fontsize=10)
    ax_c.set_ylabel("VRR (%)", fontsize=10)
    ax_c.grid(True, linestyle=":", alpha=0.6)
    ax_c.legend(frameon=True, fontsize=9)

    # Panel D: Interaction: EV vs Gasoline/Flex inside each Price Bracket
    ax_d = axes[1, 1]
    palette = {"Elétrico": "#17becf", "Gasolina": "#1f77b4", "Flex": "#ff7f0e", "Híbrido": "#2ca02c"}
    grouped = pdf.groupby(["segmento_preco", "nome_combustivel"])["delta_vrr"].median().reset_index()
    # Filter for representative fuels
    grouped = grouped[grouped["nome_combustivel"].isin(["Elétrico", "Gasolina", "Flex", "Híbrido"])]
    
    segments = ["Entrada", "Intermediario", "Luxo"]
    x = np.arange(len(segments))
    width = 0.2
    
    fuels_to_plot = ["Elétrico", "Híbrido", "Gasolina", "Flex"]
    for i, f_name in enumerate(fuels_to_plot):
        vals = []
        for s in segments:
            sub = grouped[(grouped["segmento_preco"] == s) & (grouped["nome_combustivel"] == f_name)]
            vals.append(sub["delta_vrr"].values[0] if len(sub) > 0 else 0)
        ax_d.bar(x + (i - 1.5) * width, vals, width, label=f_name, color=palette[f_name])

    ax_d.set_xticks(x)
    ax_d.set_xticklabels(segments, fontsize=10, fontweight="bold")
    ax_d.axhline(0, color="black", linestyle="-", linewidth=0.8)
    ax_d.set_title("D. Variação Mediana de VRR (32m): Combustível dentro da Faixa", fontsize=11, fontweight="bold")
    ax_d.set_ylabel("Delta VRR Mediano (%)", fontsize=10)
    ax_d.grid(True, linestyle=":", alpha=0.6, axis="y")
    ax_d.legend(frameon=True, fontsize=9)

    plt.suptitle("Diagnóstico: O Agrupamento Identifica Combustível ou Faixa de Valor?", fontsize=14, fontweight="bold", y=0.995)
    plt.tight_layout()
    plot_path = clustering_dir / "clustering_fuel_vs_price_diagnostic.png"
    fig.savefig(plot_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

    # 5. Export summary JSON
    results = {
        "metrics": metrics,
        "anova": {
            "sum_sq_fuel": float(anova_table.loc["C(nome_combustivel)", "sum_sq"]),
            "f_fuel": float(anova_table.loc["C(nome_combustivel)", "F"]),
            "p_fuel": float(anova_table.loc["C(nome_combustivel)", "PR(>F)"]),
            "sum_sq_seg": float(anova_table.loc["C(segmento_preco)", "sum_sq"]),
            "f_seg": float(anova_table.loc["C(segmento_preco)", "F"]),
            "p_seg": float(anova_table.loc["C(segmento_preco)", "PR(>F)"]),
        },
        "fuel_distribution_pct": ct_fuel_pct.to_dict(),
        "segment_distribution_pct": ct_seg_pct.to_dict(),
    }
    with open(clustering_dir / "fuel_vs_price_evaluation.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("Diagnostic complete!")
    print(f"Figure saved to: {plot_path}")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    run_evaluation()
