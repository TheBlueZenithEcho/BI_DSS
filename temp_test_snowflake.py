import sys
sys.path.append('d:/Workspace/BI/dss_hotel_analytics')
from src.ingestion.snowflake_ingest import get_connection

conn = get_connection()
cur = conn.cursor()
cur.execute('SELECT CURRENT_ACCOUNT()')
print('Account:', cur.fetchone())
cur.execute('SELECT CURRENT_WAREHOUSE()')
print('Warehouse:', cur.fetchone())
cur.execute('SELECT CURRENT_DATABASE()')
print('Database:', cur.fetchone())
cur.close()
conn.close()

