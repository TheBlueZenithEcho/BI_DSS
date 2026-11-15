{{ config(materialized='table') }}

select
    "raw_booking_id"::number(38,0) as raw_booking_id,
    coalesce(trim("market_segment"), 'Undefined') as market_segment,
    coalesce(trim("distribution_channel"), 'Undefined') as distribution_channel,
    coalesce(trim("deposit_type"), 'Undefined') as deposit_type,
    coalesce(trim("customer_type"), 'Undefined') as customer_type
from {{ ref('stg_raw_hotel_bookings') }}
