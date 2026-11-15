{{ config(materialized='table') }}

select
    "raw_booking_id"::number(38,0) as raw_booking_id,
    coalesce(trim("country"), 'Unknown') as country,
    try_to_number(to_varchar("is_repeated_guest"))::integer as is_repeated_guest,
    try_to_number(to_varchar("previous_cancellations"))::integer as previous_cancellations,
    try_to_number(to_varchar("previous_bookings_not_canceled"))::integer as previous_bookings_not_canceled
from {{ ref('stg_raw_hotel_bookings') }}
