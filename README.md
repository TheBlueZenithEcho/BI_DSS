# DSS Hotel Analytics

## Tổng quan

Repository **DSS Hotel Analytics** chứa một pipeline xử lý dữ liệu khách sạn, gồm các bước:

- **Bronze**: thu thập dữ liệu thô từ Snowflake.
- **Silver** & **Gold**: chuyển đổi dữ liệu bằng DBT (lớp chuẩn hoá và lớp doanh nghiệp).
- **Prefect**: điều phối toàn bộ quy trình, chạy ingestion, DBT và kiểm thử.

Cấu trúc dự án:

- `src/ingestion` – Logic ingest vào Snowflake (`snowflake_ingest.py`).
- `src/orchestration` – Flow Prefect (`prefect_flow.py`).
- `dbt/hotel_dwh` – Dự án DBT cho các model Silver/Gold, test và tài liệu.
- `src/diagnostics` – Các script hỗ trợ kiểm tra dữ liệu (`validate_and_kpi.py`).

## Kiến trúc

```
Bronze → Snowflake
   |
   v
Silver – DBT models
   |
   v
Gold  – DBT models
   |
   v
Prefect flow kiểm tra và chạy pipeline.
```

## Bắt đầu

### Yêu cầu trước

- **Python 3.13** (hoặc phiên bản tương thích).
- **Tài khoản Snowflake** với các biến môi trường trong file `.env` ở thư mục gốc:
  ```
  SNOWFLAKE_ACCOUNT=your_account
  SNOWFLAKE_USER=your_user
  SNOWFLAKE_PASSWORD=your_password
  SNOWFLAKE_DATABASE=YOUR_DB
  SNOWFLAKE_SCHEMA=PUBLIC
  SNOWFLAKE_WAREHOUSE=COMPUTE_WH
  ```
- **DBT** (adapter Snowflake) và **dbt‑utils** package.
- **Prefect** (≥ 3.0) và **prefect‑shell**.

### Cài đặt

1. Clone repository và chuyển vào thư mục dự án:
   ```bash
   git clone <repo-url>
   cd dss_hotel_analytics
   ```
2. Cài đặt các phụ thuộc Python:
   ```bash
   pip install -r requirements.txt
   ```
3. Cài đặt phụ thuộc DBT (chạy trong thư mục DBT):
   ```bash
   cd dbt/hotel_dwh
   dbt deps
   ```
4. Load biến môi trường:
   ```bash
   python -c "from dotenv import load_dotenv; load_dotenv()"
   ```

## Chạy pipeline

Thực thi flow Prefect:
```bash
python -m src.orchestration.prefect_flow
```
Flow sẽ thực hiện:
1. **Bronze** – ingest dữ liệu vào Snowflake.
2. **Silver** – chạy các model DBT ở layer `silver`.
3. **Gold** – chạy các model DBT ở layer `gold`.
4. **Test** – thực hiện các test DBT (bao gồm test `unique_combination_of_columns` cho `fct_daily_occupancy`).

## Các lệnh DBT

| Hành động | Lệnh |
|-----------|------|
| Biên dịch model | `dbt compile` |
| Chạy layer Silver | `dbt run --select path:models/silver` |
| Chạy layer Gold   | `dbt run --select path:models/gold` |
| Chạy tất cả test | `dbt test` |
| Thêm test mới    | Sửa file `schema.yml` tương ứng và chạy `dbt test` |





