-- Silver model: Clean hotel bookings data
WITH source AS (
    SELECT * FROM HOTEL_DWH.SILVER.stg_raw_hotel_bookings
)
SELECT
    -- Example cleaning steps (preserve original columns)
    CAST(arrival_date AS DATE) AS arrival_date,
    CAST(departure_date AS DATE) AS departure_date,
    CAST(adults AS INTEGER) AS adults,
    CAST(children AS INTEGER) AS children,
    CAST(is_repeated_guest AS BOOLEAN) AS is_repeated_guest,
    -- Preserve other columns
    *
FROM source
WHERE arrival_date IS NOT NULL
  AND departure_date IS NOT NULL