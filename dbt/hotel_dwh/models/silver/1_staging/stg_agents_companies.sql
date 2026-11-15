{{ config(materialized='table') }}

with casted as (
    select
        "raw_booking_id"::number(38,0) as raw_booking_id,
        coalesce(try_to_number(to_varchar("agent")), 0)::integer as agent_id,
        coalesce(try_to_number(to_varchar("company")), 0)::integer as company_id
    from {{ ref('stg_raw_hotel_bookings') }}
)
select
    raw_booking_id,
    agent_id,
    company_id,
    iff(company_id > 0, 1, 0)::integer as has_company
from casted
