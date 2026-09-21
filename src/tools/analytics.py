import pandas as pd

from src.config import MRTE_CLEAN_PATH


def load_mrte_data():
    return pd.read_csv(
        MRTE_CLEAN_PATH,
        parse_dates=["date"]
    )


def run_analytics(
    operation: str,
    regions: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    visitor_type: str | None = None,
    visitor_origin: str | None = None,
    product: str | None = None,
    top_n: int | None = None
):
    df = load_mrte_data()

    regions = regions or []

    # -------------------------
    # Validate operation
    # -------------------------

    valid_operations = {
        "total",
        "compare",
        "rank",
        "top",
        "trend"
    }

    if operation not in valid_operations:
        raise ValueError(
            f"Unsupported analytics operation: "
            f"{operation}"
        )

    # -------------------------
    # Region filter
    # -------------------------

    if regions:
        available_regions = {
            str(region).casefold(): region
            for region
            in df["region"]
            .dropna()
            .unique()
        }

        matched_regions = []
        missing_regions = []

        for region in regions:
            match = available_regions.get(
                str(region).casefold()
            )

            if match:
                matched_regions.append(
                    match
                )
            else:
                missing_regions.append(
                    region
                )

        if missing_regions:
            raise ValueError(
                "No regional MRTE data found for: "
                + ", ".join(
                    missing_regions
                )
            )

        df = df[
            df["region"].isin(
                matched_regions
            )
        ]

        regions = matched_regions

    # -------------------------
    # Date filter
    # -------------------------

    if start_date:
        start_timestamp = pd.Timestamp(
            start_date
        )

        df = df[
            df["date"]
            >= start_timestamp
        ]

    if end_date:
        end_timestamp = pd.Timestamp(
            end_date
        )

        df = df[
            df["date"]
            <= end_timestamp
        ]

    # If no analytics period is supplied,
    # use the latest available month,
    # except for trend analysis.
    if (
        not start_date
        and not end_date
        and operation != "trend"
    ):
        latest_date = df["date"].max()

        df = df[
            df["date"]
            == latest_date
        ]

    # -------------------------
    # Visitor type filter
    # -------------------------

    if visitor_type:
        df = df[
            df["visitor_type"]
            .fillna("")
            .str.casefold()
            == visitor_type.casefold()
        ]

    # -------------------------
    # Visitor origin filter
    # -------------------------

    if visitor_origin:
        df = df[
            df["origin"]
            .fillna("")
            .str.casefold()
            == visitor_origin.casefold()
        ]

    # -------------------------
    # Product filter
    # -------------------------

    if product:
        df = df[
            df["product"]
            .fillna("")
            .str.casefold()
            == product.casefold()
        ]

    # -------------------------
    # Empty result
    # -------------------------

    if df.empty:
        raise ValueError(
            "No matching tourism data found."
        )

    # -------------------------
    # Common metadata
    # -------------------------

    actual_start_date = (
        df["date"]
        .min()
        .strftime("%Y-%m-%d")
    )

    actual_end_date = (
        df["date"]
        .max()
        .strftime("%Y-%m-%d")
    )

    filters = {
        "regions": regions,
        "start_date": actual_start_date,
        "end_date": actual_end_date,
        "visitor_type": visitor_type,
        "visitor_origin": visitor_origin,
        "product": product
    }

    # -------------------------
    # Total
    # -------------------------

    if operation == "total":
        total = float(
            df["monthly_spend"].sum()
        )

        return {
            "operation": "total",
            "unit": "NZD million",
            "filters": filters,
            "total": round(
                total,
                2
            )
        }

    # -------------------------
    # Compare
    # -------------------------

    if operation == "compare":
        grouped = (
            df
            .groupby(
                "region",
                as_index=False
            )["monthly_spend"]
            .sum()
            .sort_values(
                "monthly_spend",
                ascending=False
            )
        )

        data = []

        for _, row in grouped.iterrows():
            data.append(
                {
                    "region": row["region"],
                    "monthly_spend_million_nzd": round(
                        float(
                            row[
                                "monthly_spend"
                            ]
                        ),
                        2
                    )
                }
            )

        return {
            "operation": "compare",
            "unit": "NZD million",
            "filters": filters,
            "data": data
        }

    # -------------------------
    # Rank
    # -------------------------

    if operation == "rank":
        grouped = (
            df
            .groupby(
                "region",
                as_index=False
            )["monthly_spend"]
            .sum()
            .sort_values(
                "monthly_spend",
                ascending=False
            )
        )

        data = []

        for index, row in grouped.reset_index(
            drop=True
        ).iterrows():
            data.append(
                {
                    "rank": index + 1,
                    "region": row["region"],
                    "monthly_spend_million_nzd": round(
                        float(
                            row[
                                "monthly_spend"
                            ]
                        ),
                        2
                    )
                }
            )

        return {
            "operation": "rank",
            "unit": "NZD million",
            "filters": filters,
            "data": data
        }

    # -------------------------
    # Top N
    # -------------------------

    if operation == "top":
        if not top_n:
            top_n = 5

        grouped = (
            df
            .groupby(
                "region",
                as_index=False
            )["monthly_spend"]
            .sum()
            .sort_values(
                "monthly_spend",
                ascending=False
            )
            .head(top_n)
        )

        data = []

        for index, row in grouped.reset_index(
            drop=True
        ).iterrows():
            data.append(
                {
                    "rank": index + 1,
                    "region": row["region"],
                    "monthly_spend_million_nzd": round(
                        float(
                            row[
                                "monthly_spend"
                            ]
                        ),
                        2
                    )
                }
            )

        return {
            "operation": "top",
            "top_n": top_n,
            "unit": "NZD million",
            "filters": filters,
            "data": data
        }

    # -------------------------
    # Trend
    # -------------------------

    if operation == "trend":
        grouped = (
            df
            .groupby(
                "date",
                as_index=False
            )["monthly_spend"]
            .sum()
            .sort_values(
                "date"
            )
        )

        data = []

        for _, row in grouped.iterrows():
            data.append(
                {
                    "date": (
                        row["date"]
                        .strftime(
                            "%Y-%m-%d"
                        )
                    ),
                    "monthly_spend_million_nzd": round(
                        float(
                            row[
                                "monthly_spend"
                            ]
                        ),
                        2
                    )
                }
            )

        return {
            "operation": "trend",
            "unit": "NZD million",
            "filters": filters,
            "data": data
        }

    raise ValueError(
        f"Unsupported analytics operation: "
        f"{operation}"
    )