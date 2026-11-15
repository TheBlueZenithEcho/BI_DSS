
"""
Xem dữ liệu từng tầng và đối chiếu KPI độc lập.

Chạy:
    python -m src.diagnostics.check_my_data

Truy vết một raw_booking_id:
    python -m src.diagnostics.check_my_data 5000

Kiến trúc:
    Bronze: CSV gốc
    Silver: Snowflake
    Gold:   Snowflake
"""

import sys
import pandas as pd

from src.common import *
from src.ingestion.snowflake_ingest import get_connection


# ============================================================
# CONFIGURATION
# ============================================================

DATABASE = "HOTEL_DWH"

BRONZE_SCHEMA = "BRONZE"
SILVER_SCHEMA = "SILVER"
GOLD_SCHEMA = "GOLD"

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)


# ============================================================
# SNOWFLAKE QUERY
# ============================================================

def query_to_df(sql):
    """Execute SQL on Snowflake and return a DataFrame."""

    conn = get_connection()

    try:
        df = pd.read_sql_query(sql, conn)

    finally:
        conn.close()

    df.columns = df.columns.str.lower()

    return df


def load_table(schema, table):
    """Load a Snowflake table."""

    return query_to_df(
        f"SELECT * FROM {DATABASE}.{schema}.{table}"
    )


# ============================================================
# DISPLAY HELPER
# ============================================================

def show_table(name, df):

    print(
        f"\n--- {name}: "
        f"{df.shape[0]:,} dòng x "
        f"{df.shape[1]} cột"
    )

    print(df.head(3).to_string(index=False))


def show_record(name, df, condition):

    result = df.loc[condition]

    print(f"\n=== {name} ===")

    if result.empty:
        print("Không tìm thấy bản ghi.")

    else:
        print(result.T.to_string())


# ============================================================
# LOAD DATA
# ============================================================

def load_all_tables():

    tables = {

        "silver/1_staging/stg_bookings":
            load_table(SILVER_SCHEMA, "STG_BOOKINGS"),

        "silver/1_staging/rejected_rows":
            load_table(SILVER_SCHEMA, "REJECTED_ROWS"),

        "silver/2_intermediate/int_booking_risk":
            load_table(SILVER_SCHEMA, "INT_BOOKING_RISK"),

        "gold/dimensions/dim_hotel":
            load_table(GOLD_SCHEMA, "DIM_HOTEL"),

        "gold/dimensions/dim_segment":
            load_table(GOLD_SCHEMA, "DIM_SEGMENT"),

        "gold/dimensions/dim_lead_bucket":
            load_table(GOLD_SCHEMA, "DIM_LEAD_BUCKET"),

        "gold/dimensions/dim_policy":
            load_table(GOLD_SCHEMA, "DIM_POLICY"),

        "gold/facts/fct_booking":
            load_table(GOLD_SCHEMA, "FCT_BOOKING"),

        "gold/facts/fct_daily_occupancy":
            load_table(GOLD_SCHEMA, "FCT_DAILY_OCCUPANCY"),
    }

    return tables


# ============================================================
# TRACE ONE BOOKING
# ============================================================

def trace_booking(raw_booking_id, tables):

    raw = read_bronze()

    # raw_booking_id trong pipeline được sinh theo index + 1.
    # Vì vậy không nên mặc định raw_booking_id luôn là vị trí dòng
    # nếu ingestion logic đã thay đổi.

    if "raw_booking_id" in raw.columns:

        raw_record = raw[
            raw["raw_booking_id"] == raw_booking_id
        ]

    else:

        raw_record = raw.iloc[[raw_booking_id - 1]]

    print("\n=== BRONZE: RAW DATA ===")

    if raw_record.empty:
        print("Không tìm thấy raw_booking_id trong Bronze.")

    else:
        print(raw_record.T.to_string())

    # Silver staging
    stg = tables["silver/1_staging/stg_bookings"]

    show_record(
        "SILVER STAGING: STG_BOOKINGS",
        stg,
        stg["raw_booking_id"] == raw_booking_id
    )

    # Silver intermediate
    it = tables["silver/2_intermediate/int_booking_risk"]

    show_record(
        "SILVER INTERMEDIATE: INT_BOOKING_RISK",
        it,
        it["raw_booking_id"] == raw_booking_id
    )

    # Gold fact
    fb = tables["gold/facts/fct_booking"]

    show_record(
        "GOLD: FCT_BOOKING",
        fb,
        fb["booking_id"] == raw_booking_id
    )

    # Rejected rows
    rejected = tables["silver/1_staging/rejected_rows"]

    if "raw_booking_id" in rejected.columns:

        show_record(
            "SILVER: REJECTED_ROWS",
            rejected,
            rejected["raw_booking_id"] == raw_booking_id
        )


# ============================================================
# SHOW TABLES
# ============================================================

def show_all_tables(tables):

    print("\n########## 1. XEM TỪNG BẢNG ##########")

    for name, df in tables.items():

        show_table(name, df)


# ============================================================
# INDEPENDENT KPI VALIDATION
# ============================================================

def validate_independent_kpi(tables):

    print(
        "\n########## 2. ĐỐI CHIẾU ĐỘC LẬP "
        "(tính lại từ file thô) ##########"
    )

    # --------------------------------------------------------
    # RAW DATA
    # --------------------------------------------------------

    raw = read_bronze().copy()

    # Nếu raw_booking_id được tạo trong ingestion nhưng không có
    # trong file CSV gốc, không sử dụng nó trong duplicate check.

    raw["nights"] = (
        raw["stays_in_weekend_nights"]
        + raw["stays_in_week_nights"]
    )

    raw["guests"] = (
        raw["adults"]
        + raw["children"].fillna(0)
        + raw["babies"]
    )

    # --------------------------------------------------------
    # CLEANING
    # --------------------------------------------------------

    raw = raw[
        (raw["guests"] > 0)
        & (raw["adr"] >= 0)
        & (raw["adr"] <= ADR_MAX)
    ].copy()

    # Loại duplicate theo các cột dữ liệu nguồn.
    # Giữ nguyên logic của script cũ.
    duplicate_columns = [
        c for c in raw.columns
        if c not in ["nights", "guests", "raw_booking_id"]
    ]

    raw = raw[
        ~raw[duplicate_columns].duplicated()
    ].copy()

    # --------------------------------------------------------
    # ARRIVAL DATE
    # --------------------------------------------------------

    arr = pd.to_datetime(
        dict(
            year=raw["arrival_date_year"],
            month=raw["arrival_date_month"].map(MONTHS),
            day=raw["arrival_date_day_of_month"]
        )
    )

    # --------------------------------------------------------
    # CANCELLATION NOTICE
    # --------------------------------------------------------

    reservation_date = pd.to_datetime(
        raw["reservation_status_date"],
        errors="coerce"
    )

    notice = (
        arr - reservation_date
    ).dt.days

    # --------------------------------------------------------
    # LATE CANCELLATION
    # --------------------------------------------------------

    late = (
        (
            (raw["is_canceled"] == 1)
            & (notice <= LATE_CANCEL_T)
        )
        |
        (raw["reservation_status"] == "No-Show")
    )

    # --------------------------------------------------------
    # ELIGIBILITY
    # --------------------------------------------------------

    elig = (
        (raw["lead_time"] >= LATE_CANCEL_T)
        &
        (
            (raw["is_canceled"] == 0)
            |
            (notice <= LATE_CANCEL_T)
        )
    )

    # --------------------------------------------------------
    # REVENUE
    # --------------------------------------------------------

    pot = raw["adr"] * raw["nights"]

    raw["potential_revenue"] = pot

    raw["realized_revenue"] = (
        pot * (raw["is_canceled"] == 0)
    )

    raw["revenue_at_risk"] = (
        pot * late
    )

    # --------------------------------------------------------
    # GOLD
    # --------------------------------------------------------

    gold = tables["gold/facts/fct_booking"]

    gold = gold[
        gold["is_duplicate"] == 0
    ].copy()

    # --------------------------------------------------------
    # KPI COMPARISON
    # --------------------------------------------------------

    raw_eligible = elig.sum()

    gold_eligible = gold["is_eligible_at_T"].sum()

    raw_p_late = (
        (late & elig).sum() / raw_eligible
        if raw_eligible > 0
        else 0
    )

    gold_p_late = (
        (
            gold["is_late_cancel"]
            * gold["is_eligible_at_T"]
        ).sum() / gold_eligible
        if gold_eligible > 0
        else 0
    )

    rows = [

        (
            "Số đơn sạch (không trùng, không lỗi)",
            len(raw),
            len(gold)
        ),

        (
            "Tỷ lệ hủy tổng",
            raw["is_canceled"].mean(),
            gold["is_canceled"].mean()
        ),

        (
            "Số đơn hủy muộn / no-show",
            int(late.sum()),
            int(gold["is_late_cancel"].sum())
        ),

        (
            "p_late toàn chuỗi",
            raw_p_late,
            gold_p_late
        ),

        (
            "Doanh thu tiềm năng (EUR)",
            raw["potential_revenue"].sum(),
            gold["potential_revenue"].sum()
        ),

        (
            "Doanh thu thực nhận (EUR)",
            raw["realized_revenue"].sum(),
            gold["realized_revenue"].sum()
        ),

        (
            "Revenue at Risk (EUR)",
            raw["revenue_at_risk"].sum(),
            gold["revenue_at_risk"].sum()
        ),
    ]

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    ok = True

    print(
        f"{'Chỉ số':42s}"
        f"{'Tính từ file thô':>20s}"
        f"{'Bảng Gold':>20s}   Khớp?"
    )

    for name, a, b in rows:

        tolerance = (
            1e-6 * max(1, abs(a))
            + 0.01
        )

        match = abs(a - b) < tolerance

        ok &= match

        print(
            f"{name:42s}"
            f"{a:>20,.4f}"
            f"{b:>20,.4f}   "
            f"{'✔' if match else '✘'}"
        )

    print(
        "\nKẾT LUẬN:",
        (
            "Gold khớp với tính toán độc lập từ file thô."
            if ok
            else "CÓ CHỖ LỆCH - cần xem lại."
        )
    )

    return ok


# ============================================================
# MAIN
# ============================================================

def main():

    tables = load_all_tables()

    # Trace mode
    if len(sys.argv) > 1:

        raw_booking_id = int(sys.argv[1])

        trace_booking(
            raw_booking_id,
            tables
        )

        return

    # Full diagnostic mode
    show_all_tables(tables)

    validate_independent_kpi(tables)


if __name__ == "__main__":
    main()
