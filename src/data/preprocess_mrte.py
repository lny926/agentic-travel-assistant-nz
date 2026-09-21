import pandas as pd

from src.config import (
    MRTE_RAW_PATH,
    MRTE_CLEAN_PATH
)


def preprocess_mrte():
    # Read the actual data sheet
    df = pd.read_excel(
        MRTE_RAW_PATH,
        sheet_name="Data base"
    )

    print("Original shape:", df.shape)

    # Rename columns to easier Python-style names
    df = df.rename(
        columns={
            "Date": "date",
            "Region": "region",
            "Product": "product",
            "Visitor Type": "visitor_type",
            "Origin": "origin",
            "Annual Spend": "annual_spend",
            "Monthly Spend": "monthly_spend"
        }
    )

    # Convert date
    df["date"] = pd.to_datetime(
        df["date"]
    )

    # Remove completely empty rows
    df = df.dropna(
        how="all"
    )

    # Remove rows missing important fields
    df = df.dropna(
        subset=[
            "date",
            "region",
            "monthly_spend"
        ]
    )

    # Make sure spend columns are numeric
    df["annual_spend"] = pd.to_numeric(
        df["annual_spend"],
        errors="coerce"
    )

    df["monthly_spend"] = pd.to_numeric(
        df["monthly_spend"],
        errors="coerce"
    )

    # Sort data
    df = df.sort_values(
        by=[
            "date",
            "region",
            "visitor_type",
            "product",
            "origin"
        ]
    )

    # Create output folder if needed
    MRTE_CLEAN_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save clean CSV
    df.to_csv(
        MRTE_CLEAN_PATH,
        index=False
    )

    print("Clean shape:", df.shape)
    print("Date range:")
    print(
        df["date"].min(),
        "->",
        df["date"].max()
    )

    print("\nRegions:")
    print(
        sorted(
            df["region"]
            .dropna()
            .unique()
        )
    )

    print("\nVisitor types:")
    print(
        df["visitor_type"]
        .value_counts()
    )

    print("\nProducts:")
    print(
        df["product"]
        .dropna()
        .unique()
    )

    print(
        "\nSaved to:",
        MRTE_CLEAN_PATH
    )


if __name__ == "__main__":
    preprocess_mrte()