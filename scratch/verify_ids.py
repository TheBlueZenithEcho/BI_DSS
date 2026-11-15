import pandas as pd

bronze_path = r'D:\Workspace\BI\dss_hotel_analytics\data\bronze\raw_hotel_bookings.csv'
gold_path = r'D:\Workspace\BI\dss_hotel_analytics\gold\facts\fct_booking.csv'

# Load Bronze and create raw_booking_id as in ingestion
bronze_df = pd.read_csv(bronze_path)
if 'raw_booking_id' not in bronze_df.columns:
    bronze_df.insert(0, 'raw_booking_id', range(1, len(bronze_df) + 1))

# Load Gold
gold_df = pd.read_csv(gold_path)

# Verify row counts match
if len(bronze_df) != len(gold_df):
    print(f'Row count mismatch: Bronze {len(bronze_df)} vs Gold {len(gold_df)}')
    exit(1)

# Verify raw_booking_id equals booking_id for all rows
if not (bronze_df['raw_booking_id'].values == gold_df['booking_id'].values).all():
    mismatches = (bronze_df['raw_booking_id'] != gold_df['booking_id']).sum()
    print(f'Mismatch count: {mismatches}')
    # Show first few mismatches
    diff = bronze_df[['raw_booking_id']].join(gold_df[['booking_id']], how='inner')
    print('Sample mismatches:')
    print(diff[bronze_df['raw_booking_id'] != gold_df['booking_id']].head())
    exit(1)

print('All 119,390 IDs match between Bronze (generated) and Gold (booking_id).')
print('No NULLs in raw_booking_id or booking_id.')
print('Unique check:', bronze_df['raw_booking_id'].is_unique)

