
  
    

create or replace transient table HOTEL_DWH.SILVER.stg_segments
    
    
    
    
    

    as (

with __dbt__cte__stg_raw_hotel_bookings as (


-- Thin source wrapper. All Silver models read the same Bronze relation.
-- Do not generate or reorder raw_booking_id here.
select *
from HOTEL_DWH.BRONZE.raw_hotel_bookings
) select
    "raw_booking_id"::number(38,0) as raw_booking_id,
    coalesce(trim("market_segment"), 'Undefined') as market_segment,
    coalesce(trim("distribution_channel"), 'Undefined') as distribution_channel,
    coalesce(trim("deposit_type"), 'Undefined') as deposit_type,
    coalesce(trim("customer_type"), 'Undefined') as customer_type
from __dbt__cte__stg_raw_hotel_bookings
    )
;


  