import os
import polars as pl
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"

def pre_processing(df: pl.DataFrame) -> pl.DataFrame:
    # Remove colunas duplicatas
    raw_total = df.height
    df = df.unique(subset=df.columns, keep="first")
    cooked_total = df.height
    print(f"Registros duplicados removidos: {raw_total - cooked_total:,}")


    return df

def analyze_years(df: pl.DataFrame) -> None:
    # Análise de anos
    print("Top-10 anos com mais veículos:")
    print(df.group_by("ano_modelo").len().sort("len", descending=True).head(10))

    print("Anos mais recentes (>= 2020):")
    print(df.filter(pl.col("ano_modelo") >= 2020).group_by("ano_modelo").len().sort("len", descending=True).head(10))


def main():
    # Carregar CSV (note o separador tab)
    # df = pl.read_csv(os.path.join(ASSETS_DIR, "fipex-prices-latest-merged.csv"), separator="\t")

    # Carregar Parquet (mais rápido!)
    df = pl.read_parquet(os.path.join(ASSETS_DIR,"fipex-prices-latest-merged.parquet"))

    # Estatísticas básicas
    # print(f"Total de registros: {df.height:,}")
    # print(f"Total de marcas: {df['nome_marca'].n_unique():,}")

    print("Colunas do DataFrame:")
    print(df.columns)

    # # Top 10 marcas
    # print(df.group_by("nome_marca").len().sort("len", descending=True).head(10))

    # # Top 10 Anos
    # print(df.group_by("ano_modelo").len().sort("len", descending=True).head(10))

    df = pre_processing(df)

    analyze_years(df)

    



if __name__ == "__main__":
    main()
