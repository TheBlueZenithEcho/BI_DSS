import pandas as pd

bronze_path = r'D:\Workspace\BI\dss_hotel_analytics\data\bronze\raw_hotel_bookings.csv'
gold_path = r'D:\Workspace\BI\dss_hotel_analytics\gold\facts\fct_booking.csv'

# Load Bronze and ensure raw_booking_id exists (preserve order)
bronze_df = pd.read_csv(bronze_path)
if 'raw_booking_id' not in bronze_df.columns:
    bronze_df.insert(0, 'raw_booking_id', range(1, len(bronze_df) + 1))

# Load Gold
gold_df = pd.read_csv(gold_path)

# Basic stats
print(f'Bronze rows: {len(bronze_df)}')
print(f'Gold rows: {len(gold_df)}')

# Check that all gold booking_id are present in bronze raw_booking_id
missing_ids = set(gold_df['booking_id']) - set(bronze_df['raw_booking_id'])
if missing_ids:
    print(f'ERROR: {len(missing_ids)} booking_id(s) in Gold not found in Bronze raw_booking_id.')
    print('Sample missing IDs:', list(missing_ids)[:10])
else:
    print('All Gold booking_id values exist in Bronze raw_booking_id.')

# Check for duplicates in Gold booking_id
duplicate_count = gold_df['booking_id'].duplicated().sum()
print(f'Duplicate booking_id in Gold: {duplicate_count}')

# Check for NULLs
null_raw = bronze_df['raw_booking_id'].isna().sum()
null_gold = gold_df['booking_id'].isna().sum()
print(f'NULL raw_booking_id in Bronze: {null_raw}')
print(f'NULL booking_id in Gold: {null_gold}')

# Verify that Gold rows are a subset of Bronze rows (by raw_booking_id)
subset = gold_df['booking_id'].isin(bronze_df['raw_booking_id']).all()
print('Gold IDs are subset of Bronze IDs:', subset)

