from pathlib import Path

import polars as pl

from preprocess import clean_data, preprocess_data, calculate_value_retention
from eda import run_eda
from encoding import run_encoding
from clustering import run_clustering_pipeline
from diagnostics import (
    diagnose_t0_duplicates,
    diagnose_zero_km_streams,
    diagnose_model_year_vs_launch,
)

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"


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

    df = clean_data(df)
    df = preprocess_data(df)
    df = calculate_value_retention(df)

    diagnose_t0_duplicates(df)
    diagnose_zero_km_streams(df)
    diagnose_model_year_vs_launch(df)
    run_eda(df, OUTPUT_DIR)
    run_encoding(df, OUTPUT_DIR / "encoding")
    run_clustering_pipeline(OUTPUT_DIR / "encoding", OUTPUT_DIR, target_window=32, k_optimal=4)


if __name__ == "__main__":
    main()
