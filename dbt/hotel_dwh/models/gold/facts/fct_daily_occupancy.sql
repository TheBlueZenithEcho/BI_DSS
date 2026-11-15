{{ config(materialized='table') }}

-- Grain = 1 hotel x 1 arrival-calendar night (periodic snapshot).
-- Window intentionally runs from min(arrival_date) to max(arrival_date),
-- matching the original Python implementation.
{% set tight_threshold = var('tight_night_threshold', 0.90) %}

with bookings as (
    select *
    from {{ ref('int_booking_risk') }}
),
date_bounds as (
    select
        min(arrival_date)::date as min_date,
        max(arrival_date)::date as max_date
    from bookings
),
day_offsets as (
    select row_number() over (order by seq4()) - 1 as day_offset
    from table(generator(rowcount => 10000))
),
calendar as (
    select
        dateadd(day, n.day_offset, b.min_date)::date as full_date,
        to_number(to_char(dateadd(day, n.day_offset, b.min_date), 'YYYYMMDD'))::number(8,0) as date_key
    from date_bounds b
    cross join day_offsets n
    where n.day_offset <= datediff(day, b.min_date, b.max_date)
),
hotel_calendar as (
    select h.hotel_key, h.hotel_name, c.full_date, c.date_key,
           h.capacity_dedup, h.capacity_all
    from {{ ref('dim_hotel') }} h
    cross join calendar c
),
arrival_metrics as (
    select
        h.hotel_key,
        b.arrival_date as full_date,
        count_if(b.is_duplicate = 0) as booked_arrivals_dedup,
        count_if(b.is_duplicate = 0 and b.is_canceled = 0) as actual_arrivals_dedup,
        sum(iff(b.is_duplicate = 0, b.is_late_cancel, 0)) as late_canceled_arrivals_dedup,
        count(*) as booked_arrivals_all,
        count_if(b.is_canceled = 0) as actual_arrivals_all,
        sum(b.is_late_cancel) as late_canceled_arrivals_all
    from bookings b
    inner join {{ ref('dim_hotel') }} h
        on b.hotel_name = h.hotel_name
    group by h.hotel_key, b.arrival_date
),
occupied_metrics as (
    select
        h.hotel_key,
        c.full_date,
        count_if(
            b.is_duplicate = 0
            and b.is_canceled = 0
            and b.total_nights > 0
        ) as occupied_rooms_dedup,
        count_if(
            b.is_canceled = 0
            and b.total_nights > 0
        ) as occupied_rooms_all
    from {{ ref('dim_hotel') }} h
    cross join calendar c
    left join bookings b
        on b.hotel_name = h.hotel_name
       and b.arrival_date <= c.full_date
       and b.departure_date > c.full_date
    group by h.hotel_key, c.full_date
),
combined as (
    select
        hc.hotel_key,
        hc.date_key,
        hc.capacity_dedup,
        coalesce(am.booked_arrivals_dedup, 0)::integer as booked_arrivals_dedup,
        coalesce(am.actual_arrivals_dedup, 0)::integer as actual_arrivals_dedup,
        coalesce(am.late_canceled_arrivals_dedup, 0)::integer as late_canceled_arrivals_dedup,
        coalesce(om.occupied_rooms_dedup, 0)::integer as occupied_rooms_dedup,
        hc.capacity_all,
        coalesce(am.booked_arrivals_all, 0)::integer as booked_arrivals_all,
        coalesce(am.actual_arrivals_all, 0)::integer as actual_arrivals_all,
        coalesce(am.late_canceled_arrivals_all, 0)::integer as late_canceled_arrivals_all,
        coalesce(om.occupied_rooms_all, 0)::integer as occupied_rooms_all
    from hotel_calendar hc
    left join arrival_metrics am
        on hc.hotel_key = am.hotel_key
       and hc.full_date = am.full_date
    left join occupied_metrics om
        on hc.hotel_key = om.hotel_key
       and hc.full_date = om.full_date
)
select
    hotel_key,
    date_key,
    capacity_dedup,
    booked_arrivals_dedup,
    actual_arrivals_dedup,
    late_canceled_arrivals_dedup,
    occupied_rooms_dedup,
    round(occupied_rooms_dedup / nullif(capacity_dedup, 0), 4) as occupancy_rate_dedup,
    iff(occupied_rooms_dedup / nullif(capacity_dedup, 0) >= {{ tight_threshold }}, 1, 0)::integer
        as is_tight_night_dedup,
    capacity_all,
    booked_arrivals_all,
    actual_arrivals_all,
    late_canceled_arrivals_all,
    occupied_rooms_all,
    round(occupied_rooms_all / nullif(capacity_all, 0), 4) as occupancy_rate_all,
    iff(occupied_rooms_all / nullif(capacity_all, 0) >= {{ tight_threshold }}, 1, 0)::integer
        as is_tight_night_all
from combined
