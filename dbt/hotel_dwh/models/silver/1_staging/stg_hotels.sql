{{ config(materialized='table') }}

select distinct
    trim("hotel") as hotel_name
from {{ ref('stg_raw_hotel_bookings') }}
where "hotel" is not null
order by hotel_name
