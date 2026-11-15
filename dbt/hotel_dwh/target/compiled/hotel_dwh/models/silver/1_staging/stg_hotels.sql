

with __dbt__cte__stg_raw_hotel_bookings as (


-- Thin source wrapper. All Silver models read the same Bronze relation.
-- Do not generate or reorder raw_booking_id here.
select *
from HOTEL_DWH.BRONZE.raw_hotel_bookings
) select distinct
    trim("hotel") as hotel_name
from __dbt__cte__stg_raw_hotel_bookings
where "hotel" is not null
order by hotel_name