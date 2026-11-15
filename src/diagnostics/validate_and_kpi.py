
"""
Kiểm tra chất lượng dữ liệu Gold:
- PK / FK / NULL / logic
- KPI preview
- Đọc dữ liệu trực tiếp từ Snowflake
"""

from src.common import *
import pandas as pd

# ============================================================
# CONFIGURATION
# ============================================================

# Sử dụng schema Gold hiện tại trên Snowflake.
# Nếu dbt generate_schema_name tạo schema khác, cần điều chỉnh.
DATABASE = "HOTEL_DWH"
GOLD_SCHEMA = "GOLD"

ok = True


# ============================================================
# CHECK HELPER
# ============================================================

def check(name, cond):
    global ok

    passed = bool(cond)

    ok &= passed

    print(f"  [{'OK' if passed else 'FAIL'}] {name}")


# ============================================================
# SNOWFLAKE QUERY
# ============================================================

def query_to_df(sql):
    """Execute SQL on Snowflake and return pandas DataFrame."""

    from src.ingestion.snowflake_ingest import get_connection

    conn = get_connection()

    try:
        df = pd.read_sql_query(sql, conn)

    finally:
        conn.close()

    # Snowflake column names are commonly returned in uppercase.
    # Normalize to lowercase to match the original validation logic.
    df.columns = df.columns.str.lower()

    return df


def load_gold_tables():

    print("Loading Gold tables from Snowflake...")

    fb = query_to_df(
        f"SELECT * FROM {DATABASE}.{GOLD_SCHEMA}.FCT_BOOKING"
    )

    fo = query_to_df(
        f"SELECT * FROM {DATABASE}.{GOLD_SCHEMA}.FCT_DAILY_OCCUPANCY"
    )

    dh = query_to_df(
        f"SELECT * FROM {DATABASE}.{GOLD_SCHEMA}.DIM_HOTEL"
    )

    ds = query_to_df(
        f"SELECT * FROM {DATABASE}.{GOLD_SCHEMA}.DIM_SEGMENT"
    )

    dl = query_to_df(
        f"SELECT * FROM {DATABASE}.{GOLD_SCHEMA}.DIM_LEAD_BUCKET"
    )

    dd = query_to_df(
        f"SELECT * FROM {DATABASE}.{GOLD_SCHEMA}.DIM_DATE"
    )

    return fb, fo, dh, ds, dl, dd


# ============================================================
# MAIN
# ============================================================

def main():

    global ok

    fb, fo, dh, ds, dl, dd = load_gold_tables()

    print("\n== KIỂM TRA TOÀN VẸN ==")

    # --------------------------------------------------------
    # 1. RECORD COUNT
    # --------------------------------------------------------

    check(
        "FCT_BOOKING không rỗng",
        len(fb) > 0
    )

    check(
        "FCT_DAILY_OCCUPANCY không rỗng",
        len(fo) > 0
    )

    # --------------------------------------------------------
    # 2. PRIMARY KEY
    # --------------------------------------------------------

    check(
        "booking_id là PK duy nhất",
        fb["booking_id"].is_unique
    )

    check(
        "FCT_DAILY_OCCUPANCY PK (hotel_key, date_key) duy nhất",
        not fo.duplicated(["hotel_key", "date_key"]).any()
    )

    # --------------------------------------------------------
    # 3. FOREIGN KEY
    # --------------------------------------------------------

    check(
        "FK hotel_key hợp lệ",
        fb["hotel_key"].isin(dh["hotel_key"]).all()
    )

    check(
        "FK segment_key hợp lệ",
        fb["segment_key"].isin(ds["segment_key"]).all()
    )

    check(
        "FK lead_bucket_key hợp lệ",
        fb["lead_bucket_key"].isin(dl["lead_bucket_key"]).all()
    )

    check(
        "FK hotel_key trong FCT_DAILY_OCCUPANCY hợp lệ",
        fo["hotel_key"].isin(dh["hotel_key"]).all()
    )

    for c in [
        "arrival_date_key",
        "booking_date_key",
        "departure_date_key"
    ]:

        check(
            f"{c} nằm trong DIM_DATE",
            fb[c].isin(dd["date_key"]).all()
        )

    check(
        "FCT_DAILY_OCCUPANCY date_key nằm trong DIM_DATE",
        fo["date_key"].isin(dd["date_key"]).all()
    )

    # --------------------------------------------------------
    # 4. CAPACITY VALIDATION
    # --------------------------------------------------------

    capacity = dh.set_index("hotel_key")["capacity_dedup"]

    max_occupied = (
        fo.groupby("hotel_key")["occupied_rooms_dedup"]
        .max()
    )

    capacity_check = (
        max_occupied <= capacity.reindex(max_occupied.index)
    ).all()

    check(
        "Công suất >= số phòng bận tối đa (dedup)",
        capacity_check
    )

    # --------------------------------------------------------
    # 5. NULL VALIDATION
    # --------------------------------------------------------

    required_columns = [
        "booking_id",
        "hotel_key",
        "adr",
        "potential_revenue",
        "p_late_group",
        "risk_group"
    ]

    check(
        "Không NULL ở các cột khóa/measure chính",
        fb[required_columns].notna().all().all()
    )

    # --------------------------------------------------------
    # 6. BUSINESS LOGIC
    # --------------------------------------------------------

    check(
        "p_late_group trong [0,1]",
        fb["p_late_group"].between(0, 1).all()
    )

    check(
        "is_late_cancel + is_early_cancel <= 1",
        (
            fb["is_early_cancel"] +
            fb["is_late_cancel"]
        ).le(1).all()
    )

    check(
        "realized_revenue = 0 khi hủy",
        (
            fb.loc[
                fb["is_canceled"] == 1,
                "realized_revenue"
            ] == 0
        ).all()
    )

    check(
        "cancel_notice_days chỉ có khi is_canceled = 1",
        fb.loc[
            fb["is_canceled"] == 0,
            "cancel_notice_days"
        ].isna().all()
    )

    print(
        "  cancel_notice_days < 0:",
        int((fb["cancel_notice_days"] < 0).sum()),
        "dòng"
    )

    # --------------------------------------------------------
    # 7. DATA QUALITY FLAGS
    # --------------------------------------------------------

    print("\n== CHẤT LƯỢNG DỮ LIỆU (đếm cờ) ==")

    flag_columns = [
        "is_duplicate",
        "is_zero_night",
        "is_zero_adr",
        "is_room_changed",
        "is_no_show",
        "is_late_cancel",
        "is_early_cancel"
    ]

    for c in flag_columns:

        print(
            f"  {c:18s}: "
            f"{int(fb[c].sum()):>7,} "
            f"({fb[c].mean():.2%})"
        )

    # --------------------------------------------------------
    # 8. KPI PREVIEW
    # --------------------------------------------------------

    print("\n== KPI PREVIEW (dữ liệu đã loại trùng) ==")

    d = fb[fb["is_duplicate"] == 0].copy()

    print(
        f"  Số đơn sau loại trùng: {len(d):,}"
        f"   Tỷ lệ hủy tổng: {d['is_canceled'].mean():.2%}"
    )

    eligible_count = d["is_eligible_at_T"].sum()

    if eligible_count > 0:

        p_late = (
            d["is_late_cancel"] *
            d["is_eligible_at_T"]
        ).sum() / eligible_count

        print(
            f"  p_late toàn chuỗi = {p_late:.2%}"
        )

    else:

        print("  p_late toàn chuỗi = N/A (không có đơn đủ điều kiện)")

    potential_revenue = d["potential_revenue"].sum()

    if potential_revenue > 0:

        revenue_at_risk_rate = (
            d["revenue_at_risk"].sum() /
            potential_revenue
        )

        print(
            f"  Revenue at Risk Rate = "
            f"{revenue_at_risk_rate:.2%}"
        )

    else:

        print("  Revenue at Risk Rate = N/A")

    # --------------------------------------------------------
    # 9. RISK GROUP x HOTEL
    # --------------------------------------------------------

    print("\n  Theo risk_group x hotel:")

    g = (
        d.merge(
            dh[["hotel_key", "hotel_type"]],
            on="hotel_key"
        )
        .groupby(["hotel_type", "risk_group"])
        .agg(
            don=("booking_id", "size"),
            ty_le_huy=("is_canceled", "mean"),
            p_late=("p_late_group", "mean"),
            rev_at_risk=("revenue_at_risk", "sum")
        )
    )

    print(g.round(3).to_string())

    # --------------------------------------------------------
    # 10. OCCUPANCY ANALYSIS
    # --------------------------------------------------------

    print("\n  Đêm sát kín phòng (>=90%):")

    # Use actual dedup column names.
    occ_rate_col = "occupancy_rate_dedup"
    tight_night_col = "is_tight_night_dedup"

    t = fo.merge(
        dh[["hotel_key", "hotel_type"]],
        on="hotel_key"
    )

    print(
        t.groupby("hotel_type")
        .agg(
            so_dem=("date_key", "size"),
            dem_tight=(tight_night_col, "sum"),
            occ_tb=(occ_rate_col, "mean"),
            occ_max=(occ_rate_col, "max")
        )
        .round(3)
        .to_string()
    )

    # --------------------------------------------------------
    # 11. LATE CANCELLATION BY OCCUPANCY
    # --------------------------------------------------------

    print("\n  p_late theo loại đêm đến:")

    ft = d.merge(
        fo[
            [
                "hotel_key",
                "date_key",
                tight_night_col
            ]
        ],
        left_on=[
            "hotel_key",
            "arrival_date_key"
        ],
        right_on=[
            "hotel_key",
            "date_key"
        ],
        how="left"
    )

    ft["num"] = (
        ft["is_late_cancel"] *
        ft["is_eligible_at_T"]
    )

    ft = ft.merge(
        dh[["hotel_key", "hotel_type"]],
        on="hotel_key"
    )

    r = (
        ft.groupby(
            ["hotel_type", tight_night_col]
        )
        .agg(
            el=("is_eligible_at_T", "sum"),
            num=("num", "sum")
        )
    )

    r["p_late"] = r["num"] / r["el"].replace(0, pd.NA)

    print(r.round(4).to_string())

    # --------------------------------------------------------
    # 12. RISK GROUP THRESHOLD
    # --------------------------------------------------------

    print("\n  Ngưỡng risk_group (min/max p_late_group):")

    print(
        d.merge(
            dh[["hotel_key", "hotel_type"]],
            on="hotel_key"
        )
        .groupby(
            ["hotel_type", "risk_group"]
        )["p_late_group"]
        .agg(["min", "max"])
        .round(4)
        .to_string()
    )

    # --------------------------------------------------------
    # 13. TOP SEGMENTS
    # --------------------------------------------------------

    print(
        "\n== Top 10 phân khúc "
        "(kênh x cọc x lead bucket) "
        "theo tỷ lệ hủy, >=200 đơn =="
    )

    x = (
        d.merge(ds, on="segment_key")
        .merge(dl, on="lead_bucket_key")
    )

    top = (
        x.groupby(
            [
                "distribution_channel",
                "deposit_type",
                "bucket_label"
            ]
        )
        .agg(
            don=("booking_id", "size"),
            ty_le_huy=("is_canceled", "mean")
        )
        .query("don >= 200")
        .sort_values(
            "ty_le_huy",
            ascending=False
        )
        .head(10)
    )

    print(top.round(3).to_string())

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print(
        "\nKẾT QUẢ:",
        "TẤT CẢ ĐẠT" if ok else "CÓ LỖI - xem FAIL ở trên"
    )

    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
