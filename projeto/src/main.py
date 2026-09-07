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

    # remove registros com valores nulos
    raw_total = df.height
    df = df.drop_nulls()
    cooked_total = df.height
    print(f"Registros com valores nulos removidos: {raw_total - cooked_total:,}")

    # filtra apenas carros após 2010
    raw_total = df.height
    df = df.filter(pl.col("ano_modelo") >= 2010)
    cooked_total = df.height
    print(f"Registros com ano_modelo < 2010 removidos: {raw_total - cooked_total:,}")

    # filtra apenas tipo_veiculo == "carro"
    raw_total = df.height
    df = df.filter(pl.col("tipo_veiculo") == "carro")
    cooked_total = df.height
    print(
        f"Registros com tipo_veiculo != 'carro' removidos: {raw_total - cooked_total:,}"
    )

    # imprime quantidade de codigos_fipe unicos
    print(f"Total de codigos_fipe unicos: {df['codigo_fipe'].n_unique():,}")

    print(f"Total de registros após pré-processamento: {df.height:,}")

    return df


def analyze_years(df: pl.DataFrame) -> None:
    # Análise de anos
    # print("Top-10 anos com mais veículos:")
    # print(df.group_by("ano_modelo").len().sort("len", descending=True).head(10))

    # print("Anos mais recentes (>= 2020):")
    # print(
    #     df.filter(pl.col("ano_modelo") >= 2020)
    #     .group_by("ano_modelo")
    #     .len()
    #     .sort("len", descending=True)
    #     .head(10)
    # )

    # quantidade de veiculos por decada
    print("Quantidade de veículos por década:")
    df = df.with_columns((pl.col("ano_modelo") // 10 * 10).alias("decada"))
    print(df.group_by("decada").len().sort("decada", descending=False))


def analyze_fuel_types(df: pl.DataFrame) -> None:
    # Análise de tipos de combustível
    print("Tipos de combustível:")
    resultado = (
        # 1. Ordenamos por ano para garantir a ordem cronológica
        df.sort("ano_modelo")
        # 2. Agrupamos por combustível
        .group_by("nome_combustivel").agg(
            [
                # Conta o total de carros desse combustível
                pl.len().alias("quantidade"),
                # Pega o primeiro ano e o primeiro modelo (mais antigo)
                pl.col("ano_modelo").first().alias("primeiro_ano"),
                pl.col("nome_modelo").first().alias("modelo_mais_antigo"),
                # Pega o último ano e o último modelo (mais novo)
                pl.col("ano_modelo").last().alias("mais_novo_ano"),
                pl.col("nome_modelo").last().alias("modelo_mais_novo"),
            ]
        )
        # 3. Ordena o resultado final pelos mais comuns
        .sort("quantidade", descending=True)
    )

    print(resultado)


def analyze_brands(df: pl.DataFrame) -> None:
    # Análise de marcas
    print("Top-10 marcas com mais veículos:")
    print(df.group_by("nome_marca").len().sort("len", descending=True).head(10))


def analyze_vehicle_types(df: pl.DataFrame) -> None:
    # Análise de tipos de veículos
    print("Tipos de veículos:")
    print(df.group_by("tipo_veiculo").len().sort("len", descending=True))


def main():
    # Carregar CSV (note o separador tab)
    # df = pl.read_csv(os.path.join(ASSETS_DIR, "fipex-prices-latest-merged.csv"), separator="\t")

    # Carregar Parquet (mais rápido!)
    df = pl.read_parquet(os.path.join(ASSETS_DIR, "fipex-prices-latest-merged.parquet"))

    # Estatísticas básicas
    print(f"Total de registros: {df.height:,}")
    # print(f"Total de marcas: {df['nome_marca'].n_unique():,}")

    print("Colunas do DataFrame:")
    print(df.columns)

    # # Top 10 marcas
    # print(df.group_by("nome_marca").len().sort("len", descending=True).head(10))

    # # Top 10 Anos
    # print(df.group_by("ano_modelo").len().sort("len", descending=True).head(10))

    df = pre_processing(df)

    # analyze_years(df)
    analyze_fuel_types(df)
    # analyze_brands(df)
    # analyze_vehicle_types(df)


if __name__ == "__main__":
    main()
