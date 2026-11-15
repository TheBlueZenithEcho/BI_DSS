"""Cấu hình & hàm tiện ích dùng chung cho toàn bộ pipeline Medallion.

Các hằng số đường dẫn và biến môi trường Snowflake được định nghĩa ở đây để các
module khác có thể import trực tiếp.
"""
from pathlib import Path
import os
import pandas as pd

# Root of the repository (two levels up from this file)
ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------
# Data paths (thư mục data/...) – phù hợp với kiến trúc Medallion
# ---------------------------------------------------------------------
BRONZE_FILE = ROOT / "data" / "bronze" / "raw_hotel_bookings.csv"
STG = ROOT / "data" / "silver" / "staging"
INT = ROOT / "data" / "silver" / "intermediate"
DIM = ROOT / "data" / "gold" / "dimensions"
FACT = ROOT / "data" / "gold" / "facts"

# ---------------------------------------------------------------------
# Tham số nghiệp vụ (business parameters)
# ---------------------------------------------------------------------
LATE_CANCEL_T = 7        # Ngưỡng T ngày xét hủy muộn
MIN_GROUP_SIZE = 300     # Nhóm có < 300 đơn eligible thì lùi cấp thô hơn
ADR_MAX = 1000           # adr > 1000 EUR coi là outlier
TIGHT_NIGHT_THRESHOLD = 0.90

CAPACITY_DEDUP = {"City Hotel": 216, "Resort Hotel": 184}
CAPACITY_RAW = {"City Hotel": 226, "Resort Hotel": 187}

MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], start=1)}

LEAD_BUCKETS = [
    (1, "0-7d", 0, 7), (2, "8-30d", 8, 30), (3, "31-90d", 31, 90),
    (4, "91-180d", 91, 180), (5, "181-365d", 181, 365), (6, ">365d", 366, 9999)
]

# ---------------------------------------------------------------------
# Snowflake connection variables – đọc từ môi trường.
# Người dùng nên thiết lập SNOWFLAKE_PASSWORD ngoài .env để không ghi
# mật khẩu vào repo.
# ---------------------------------------------------------------------
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA", "BRONZE")
# Password được lấy từ biến môi trường SNOWFLAKE_PASSWORD riêng biệt
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")

# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------
def read_bronze() -> pd.DataFrame:
    """Read local Bronze CSV file (fallback for local dev)."""
    return pd.read_csv(BRONZE_FILE)

def save(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"  -> {path.relative_to(ROOT)}  ({len(df):,} dòng x {df.shape[1]} cột)")

def load(path: Path, date_cols=()) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=list(date_cols))

def date_key(s: pd.Series) -> pd.Series:
    """Date → số nguyên YYYYMMDD."""
    return (s.dt.year * 10000 + s.dt.month * 100 + s.dt.day).astype("int64")
