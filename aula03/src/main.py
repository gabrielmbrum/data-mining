import matplotlib.pyplot as plt
from sklearn.datasets import load_digits
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.manifold import MDS, TSNE
from sklearn.preprocessing import StandardScaler


def main():
    # 1. Carregamento e normalização
    digits = load_digits()
    X, y = digits.data, digits.target
    X_scaled = StandardScaler().fit_transform(X)

    # 2. Execução das 4 transformações
    # Obs: Adicionado init='random' para suprimir o FutureWarning do MDS
    projections = {
        "PCA": PCA(n_components=2, random_state=42).fit_transform(X_scaled),
        "Truncated SVD": TruncatedSVD(n_components=2, random_state=42).fit_transform(
            X_scaled
        ),
        "t-SNE (Perplexity=30)": TSNE(
            n_components=2, perplexity=30, random_state=42, init="pca"
        ).fit_transform(X_scaled),
        "MDS": MDS(
            n_components=2,
            normalized_stress="auto",
            random_state=42,
            n_init=4,
            init="random",
            n_jobs=-1,
        ).fit_transform(X_scaled),
    }

    # 3. Grid 2x2
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes_flat = axes.ravel()

    last_scatter = None
    for idx, (title, data_2d) in enumerate(projections.items()):
        ax = axes_flat[idx]
        last_scatter = ax.scatter(
            data_2d[:, 0],
            data_2d[:, 1],
            c=y,
            cmap="tab10",
            alpha=0.7,
            s=12,
            edgecolors="none",
        )
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlabel("Dimensão 1")
        ax.set_ylabel("Dimensão 2")
        ax.grid(True, linestyle="--", alpha=0.3)

    # Ajuste de layout manual seguro para evitar colisões no Tkinter
    plt.subplots_adjust(bottom=0.15, hspace=0.3, wspace=0.25)

    # Barra de cores horizontal posicionada explicitamente
    cbar_ax = fig.add_axes([0.15, 0.05, 0.7, 0.03])
    cbar = fig.colorbar(
        last_scatter, cax=cbar_ax, orientation="horizontal", ticks=range(10)
    )
    cbar.set_label("Dígitos (0 a 9)", fontsize=11)

    plt.savefig("../projecoes.png", dpi=300, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    main()
