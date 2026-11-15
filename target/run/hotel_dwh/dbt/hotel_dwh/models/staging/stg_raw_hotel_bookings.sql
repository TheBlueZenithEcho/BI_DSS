
  create or replace   view HOTEL_DWH.SILVER.stg_raw_hotel_bookings
  
  
  
  
  as (
    -- Staging model for raw hotel bookings
WITH source AS (
    SELECT * FROM HOTEL_DWH.bronze.raw_hotel_bookings
)
SELECT *
FROM source
  );

