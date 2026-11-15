{{ config(materialized='ephemeral') }}

-- Thin source wrapper. All Silver models read the same Bronze relation.
-- Do not generate or reorder raw_booking_id here.
select *
from {{ source('bronze', 'raw_hotel_bookings') }}
