
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load environment variables before importing project modules
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Add project root to Python path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# 2. ENVIRONMENT VARIABLES
# ============================================================

SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")

SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")

SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")

TABLE_NAME = "RAW_HOTEL_BOOKINGS"


# ============================================================
# 3. IMPORT PROJECT MODULES
# ============================================================

from src.common import read_bronze


# ============================================================
# 4. IMPORT SNOWFLAKE CONNECTOR
# ============================================================

try:
    import snowflake.connector
    from snowflake.connector.pandas_tools import write_pandas

except ImportError as e:
    raise ImportError(
        "Cannot import Snowflake Connector or its dependencies.\n"
        'Run: python -m pip install "snowflake-connector-python[pandas]"'
    ) from e


# ============================================================
# 5. VALIDATE CONFIGURATION
# ============================================================

def validate_config():
    """Validate required Snowflake environment variables."""

    required_vars = {
        "SNOWFLAKE_ACCOUNT": SNOWFLAKE_ACCOUNT,
        "SNOWFLAKE_USER": SNOWFLAKE_USER,
        "SNOWFLAKE_PASSWORD": SNOWFLAKE_PASSWORD,
        "SNOWFLAKE_DATABASE": SNOWFLAKE_DATABASE,
        "SNOWFLAKE_WAREHOUSE": SNOWFLAKE_WAREHOUSE,
        "SNOWFLAKE_SCHEMA": SNOWFLAKE_SCHEMA,
    }

    missing = [
        name
        for name, value in required_vars.items()
        if not value or not value.strip()
    ]

    if missing:
        raise RuntimeError(
            f"Missing environment variables: {', '.join(missing)}"
        )


# ============================================================
# 6. SQL IDENTIFIER HELPERS
# ============================================================

def quote_identifier(identifier: str) -> str:
    """Safely quote a Snowflake identifier."""

    return '"' + str(identifier).replace('"', '""') + '"'


def get_table_fqn() -> str:
    """Return fully qualified Snowflake table name."""

    return ".".join(
        quote_identifier(name)
        for name in [
            SNOWFLAKE_DATABASE,
            SNOWFLAKE_SCHEMA,
            TABLE_NAME,
        ]
    )


# ============================================================
# 7. CREATE SNOWFLAKE CONNECTION
# ============================================================

def get_connection():
    """Establish Snowflake connection."""

    validate_config()

    print("[Snowflake] Connecting...")

    try:
        conn = snowflake.connector.connect(
            account=SNOWFLAKE_ACCOUNT,
            user=SNOWFLAKE_USER,
            password=SNOWFLAKE_PASSWORD,
            warehouse=SNOWFLAKE_WAREHOUSE,
            database=SNOWFLAKE_DATABASE,
            schema=SNOWFLAKE_SCHEMA,
            role=SNOWFLAKE_ROLE,
            authenticator="snowflake",
            enable_server_session_keep_alive_auto_detection=True,
        )

        print("[Snowflake] Connection successful!")

        return conn

    except snowflake.connector.errors.Error as e:
        raise RuntimeError(
            f"Snowflake connection failed: {e}"
        ) from e


# ============================================================
# 8. INITIALIZE BRONZE SCHEMA
# ============================================================

def initialize_bronze_schema(conn):
    """Ensure database, warehouse and Bronze schema are selected."""

    database = quote_identifier(SNOWFLAKE_DATABASE)
    warehouse = quote_identifier(SNOWFLAKE_WAREHOUSE)
    schema = quote_identifier(SNOWFLAKE_SCHEMA)

    with conn.cursor() as cursor:

        # Create database if it does not exist
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {database}"
        )

        # Select warehouse and database
        cursor.execute(f"USE WAREHOUSE {warehouse}")
        cursor.execute(f"USE DATABASE {database}")

        # Create Bronze schema if it does not exist
        cursor.execute(
            f"CREATE SCHEMA IF NOT EXISTS {database}.{schema}"
        )

        cursor.execute(f"USE SCHEMA {schema}")

        # Verify current session
        cursor.execute("""
            SELECT
                CURRENT_DATABASE(),
                CURRENT_SCHEMA(),
                CURRENT_WAREHOUSE(),
                CURRENT_ROLE()
        """)

        context = cursor.fetchone()

    print("[Snowflake] Context initialized:")
    print(f"    Database : {context[0]}")
    print(f"    Schema   : {context[1]}")
    print(f"    Warehouse: {context[2]}")
    print(f"    Role     : {context[3]}")


# ============================================================
# 9. MAP PANDAS TYPES TO SNOWFLAKE TYPES
# ============================================================

def get_snowflake_type(dtype):
    """Map pandas data types to Snowflake SQL data types."""

    if pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"

    if pd.api.types.is_integer_dtype(dtype):
        return "NUMBER(38,0)"

    if pd.api.types.is_float_dtype(dtype):
        return "FLOAT"

    if pd.api.types.is_datetime64_any_dtype(dtype):
        if getattr(dtype, "tz", None) is not None:
            return "TIMESTAMP_TZ"

        return "TIMESTAMP_NTZ"

    # Raw CSV text and other object columns
    return "VARCHAR"


# ============================================================
# 10. CREATE TARGET TABLE
# ============================================================

def create_target_table(conn, df: pd.DataFrame):
    """
    Explicitly create the target table before write_pandas.

    This prevents COPY INTO from targeting a missing table.
    """

    if len(df.columns) == 0:
        raise ValueError("DataFrame has no columns.")

    column_definitions = []

    for column in df.columns:

        column_name = quote_identifier(column)
        snowflake_type = get_snowflake_type(df[column].dtype)

        column_definitions.append(
            f"{column_name} {snowflake_type}"
        )

    columns_sql = ",\n".join(column_definitions)

    table_fqn = get_table_fqn()

    sql = f"""
        CREATE TABLE IF NOT EXISTS {table_fqn}
        (
            {columns_sql}
        )
    """

    with conn.cursor() as cursor:
        cursor.execute(sql)

    print(f"[Snowflake] Target table ready: {table_fqn}")


# ============================================================
# 11. LOAD LOCAL BRONZE DATA
# ============================================================

def load_local_bronze() -> pd.DataFrame:
    """Read local Bronze dataset."""

    print("[Ingestion] Reading local Bronze data...")

    df = read_bronze()

    if df is None:
        raise ValueError("read_bronze() returned None.")

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Bronze data must be a pandas DataFrame.")

    if df.empty:
        raise ValueError("Bronze dataset is empty.")

    # Normalize column names to strings
    df = df.copy()
    df.columns = [str(column) for column in df.columns]

    if not df.columns.is_unique:
        raise ValueError("DataFrame contains duplicate column names.")

    # Generate raw ID if source does not contain one
    if "raw_booking_id" not in df.columns:
        df.insert(
            0,
            "raw_booking_id",
            range(1, len(df) + 1)
        )

    print(f"[Ingestion] Rows    : {len(df):,}")
    print(f"[Ingestion] Columns : {len(df.columns)}")

    return df


# ============================================================
# 12. VERIFY SNOWFLAKE DATA
# ============================================================

def verify_loaded_data(conn, expected_rows: int):
    """Verify the number of rows in the target table."""

    table_fqn = get_table_fqn()

    with conn.cursor() as cursor:

        cursor.execute(
            f"SELECT COUNT(*) FROM {table_fqn}"
        )

        total_rows = cursor.fetchone()[0]

    print("[Verification]")
    print(f"    Expected rows: {expected_rows:,}")
    print(f"    Actual rows  : {total_rows:,}")

    if total_rows != expected_rows:
        raise RuntimeError(
            "Row count verification failed. "
            f"Expected {expected_rows:,}, got {total_rows:,}."
        )

    return total_rows


# ============================================================
# 13. BRONZE INGESTION PIPELINE
# ============================================================

def ingest_bronze_to_snowflake():
    """Load local Bronze CSV data into Snowflake."""

    print("\n" + "=" * 65)
    print("       BRONZE TO SNOWFLAKE INGESTION")
    print("=" * 65)

    conn = None

    try:
        # Step 1: Read source data
        df = load_local_bronze()

        # Step 2: Connect to Snowflake
        conn = get_connection()

        # Step 3: Initialize Snowflake objects
        initialize_bronze_schema(conn)

        # Step 4: Create target table explicitly
        create_target_table(conn, df)

        # Step 5: Upload DataFrame
        print("\n[Ingestion] Uploading data...")

        success, nchunks, nrows, output = write_pandas(
            conn=conn,
            df=df,
            table_name=TABLE_NAME,
            database=SNOWFLAKE_DATABASE,
            schema=SNOWFLAKE_SCHEMA,
            auto_create_table=False,
            overwrite=True,
            quote_identifiers=True,
        )

        if not success:
            raise RuntimeError(
                f"Upload failed. Chunks: {nchunks}, Rows: {nrows}"
            )

        # Step 6: Verify loaded data
        total_rows = verify_loaded_data(
            conn,
            expected_rows=len(df)
        )

        print("\n" + "=" * 65)
        print("[SUCCESS] BRONZE INGESTION COMPLETED")
        print("=" * 65)

        print(f"Uploaded rows : {nrows:,}")
        print(f"Chunks        : {nchunks}")
        print(f"Verified rows : {total_rows:,}")
        print(f"Destination   : {get_table_fqn()}")

        print("=" * 65)

        return {
            "success": True,
            "uploaded_rows": nrows,
            "total_rows": total_rows,
            "chunks": nchunks,
        }

    except Exception as e:

        print("\n[ERROR] BRONZE INGESTION FAILED")
        print(f"Reason: {e}")

        raise

    finally:

        if conn is not None:
            conn.close()
            print("[Snowflake] Connection closed.")


# ============================================================
# 14. MAIN
# ============================================================

if __name__ == "__main__":
    ingest_bronze_to_snowflake()
