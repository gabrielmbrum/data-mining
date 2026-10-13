import os
import polars as pl
from pathlib import Path
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"


def view(df: pl.DataFrame, n: int = 5) -> None:
    print(df.columns)
    print(df.glimpse())
    print(df.sample(n))
    print(f"\nTotal de registros: {df.height:,}")
    print(f"Total de colunas: {df.width:,}")


def clean(df: pl.DataFrame) -> pl.DataFrame:
    # Tamanho inicial
    print(f"Tamanho inicial do DataFrame: {df.height:,} registros")

    # Remove registros duplicados
    raw_total = df.height
    df = df.unique(subset=df.columns, keep="first")
    cooked_total = df.height
    print(f"Registros duplicados removidos: {raw_total - cooked_total:,}")

    # # Analisa quais campos tem valores nulos
    # null_counts = df.null_count()

    # # Transforma a primeira (e única) linha em um dicionário para exibir
    # null_dict = null_counts.row(0, named=True)

    # print("\n--- Análise de Nulos por Coluna ---")
    # tem_nulos = False
    # for col, count in null_dict.items():
    #     if count > 0:
    #         print(f"Coluna '{col}': {count} valores nulos")
    #         tem_nulos = True

    # if not tem_nulos:
    #     print("Nenhuma coluna possui valores nulos.")
    # print("-----------------------------------\n")

    # Remove registros com valores nulos
    raw_total = df.height
    df = df.drop_nulls()
    cooked_total = df.height
    print(f"Registros com valores nulos removidos: {raw_total - cooked_total:,}")

    # Limpa registros com valor zerado
    total_antes = df.height
    nao_zerados = df.filter(pl.col("valor_centavos") != 0).height
    print(f"Registros com valores zerados removidos: {total_antes - nao_zerados:,}")

    return df


def pre_processing(df: pl.DataFrame) -> pl.DataFrame:
    # filtra apenas tipo_veiculo == "carro"
    raw_total = df.height
    df = df.filter(pl.col("tipo_veiculo") == "carro")
    cooked_total = df.height
    print(
        f"Registros com tipo_veiculo != 'carro' removidos: {raw_total - cooked_total:,}"
    )

    # agrega ano_referencia e mes_referencia em uma coluna data_referencia
    df = df.with_columns(
        pl.date(pl.col("ano_referencia"), pl.col("mes_referencia"), 1).alias(
            "data_referencia"
        )
    ).drop(["ano_referencia", "mes_referencia"])

    # # filtra apenas carros após 2010
    # raw_total = df.height
    # df = df.filter(pl.col("ano_modelo") >= 2010)
    # cooked_total = df.height
    # print(f"Registros com ano_modelo < 2010 removidos: {raw_total - cooked_total:,}")

    # imprime quantidade de codigos_fipe unicos
    # print(f"Total de codigos_fipe unicos: {df['codigo_fipe'].n_unique():,}")

    # print(f"Total de registros após filtro: {df.height:,}")

    return df


def view_fuel(df: pl.DataFrame) -> None:
    tabela = (
        df.group_by(["sigla_combustivel", "nome_combustivel"])
        .len(name="quantidade_amostras")
        .sort("quantidade_amostras", descending=True)
    )

    # Configura o Polars temporariamente para não cortar linhas nem colunas no print
    with pl.Config(tbl_rows=-1, tbl_cols=-1):
        print(tabela)


def plotar_distribuicao_temporal(df: pl.DataFrame):
    # 1. Agrupa por ano extraído de data_referencia e por sigla_combustivel
    df_agrupado = (
        df.with_columns(pl.col("data_referencia").dt.year().alias("ano"))
        .group_by(["ano", "sigla_combustivel"])
        .len(name="quantidade")
        .sort("ano")
    )

    # 2. Pivota a tabela para que cada combustível vire uma coluna
    df_pivot = (
        df_agrupado.pivot(values="quantidade", index="ano", on="sigla_combustivel")
        .fill_null(0)
        .sort("ano")
    )

    # Mostra a tabela no terminal para conferência
    print("\n--- Quantidade de Registros por Ano e Combustível ---")
    with pl.Config(tbl_rows=-1, tbl_cols=-1):
        print(df_pivot)

    # 3. Configuração de estilo para os combustíveis (Nome, Cor, Estilo da Linha, Marcador)
    estilos = {
        "g": ("Gasolina (g)", "#1f77b4", "--", "o"),
        "d": ("Diesel (d)", "#ff7f0e", "--", "s"),
        "f": ("Flex (f)", "#2ca02c", "-.", "^"),
        "e": ("Álcool (e)", "#9467bd", ":", "v"),
        "h": ("Híbrido (h)", "#17becf", "-", "D"),
        "l": ("Elétrico (l)", "#d62728", "-", "*"),
        "n": ("Gás Natural (n)", "#7f7f7f", ":", "x"),
    }

    anos = df_pivot["ano"].to_list()
    colunas_comb = [col for col in df_pivot.columns if col != "ano"]
    total_por_ano = (
        df_pivot.select(pl.sum_horizontal(colunas_comb)).to_series().to_list()
    )

    # 4. Criação e salvamento de duas figuras separadas
    configuracoes = [
        (False, "distribuicao_temporal_linear.png"),
        (True, "distribuicao_temporal_log.png"),
    ]

    for is_log, nome_arquivo in configuracoes:
        fig, ax = plt.subplots(figsize=(9, 6))

        # Plota a linha de Total Geral
        ax.plot(
            anos,
            total_por_ano,
            label="Total Geral",
            color="black",
            linestyle="-",
            linewidth=2.5,
            alpha=0.8,
        )

        # Plota cada combustível
        for sigla, (rotulo, cor, estilo_linha, marcador) in estilos.items():
            if sigla in df_pivot.columns:
                valores = df_pivot[sigla].to_list()
                if is_log:
                    valores = [v if v > 0 else None for v in valores]

                espessura = 2.2 if sigla in ["l", "h"] else 1.5

                ax.plot(
                    anos,
                    valores,
                    label=rotulo,
                    color=cor,
                    linestyle=estilo_linha,
                    marker=marcador,
                    markersize=5,
                    linewidth=espessura,
                )

        ax.set_xlabel("Ano de Referência", fontsize=11)
        ax.grid(True, which="both", linestyle=":", alpha=0.6)

        if is_log:
            ax.set_yscale("log")
            ax.set_title(
                "Distribuição Temporal por Combustível (Escala Logarítmica)",
                fontsize=12,
                fontweight="bold",
            )
            ax.set_ylabel("Quantidade de Registros (Escala Log)", fontsize=11)
        else:
            ax.set_title(
                "Distribuição Temporal por Combustível (Escala Linear)",
                fontsize=12,
                fontweight="bold",
            )
            ax.set_ylabel("Quantidade de Registros", fontsize=11)

        # Adiciona a legenda individual em cada figura
        ax.legend(
            loc="upper left",
            bbox_to_anchor=(1.02, 1),
            frameon=True,
            title="Combustível",
        )

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / nome_arquivo, dpi=300, bbox_inches="tight")
        print(f"Gráfico salvo com sucesso: {nome_arquivo}")
        plt.close(fig)  # Libera a memória da figura após salvar


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
    df = pl.read_parquet(os.path.join(ASSETS_DIR, "fipex-prices-latest-merged.parquet"))

    # view(df)

    # # Top 10 marcas
    # print(df.group_by("nome_marca").len().sort("len", descending=True).head(10))

    # # Top 10 Anos
    # print(df.group_by("ano_modelo").len().sort("len", descending=True).head(10))

    df = clean(df)
    df = pre_processing(df)
    # df = view_fuel(df)

    # view(df)

    plotar_distribuicao_temporal(df)


if __name__ == "__main__":
    main()
