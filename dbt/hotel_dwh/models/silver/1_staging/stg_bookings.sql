{{ config(materialized='table') }}

-- Preserve the legacy rule: duplicate detection uses all 32 source columns,
-- before quarantine, and the smallest Bronze raw_booking_id is the first row.
with source as (
    select *
    from {{ ref('stg_raw_hotel_bookings') }}
),
marked as (
    select
        source.*,
        iff(
            row_number() over (
                partition by
                    "hotel",
                    "is_canceled",
                    "lead_time",
                    "arrival_date_year",
                    "arrival_date_month",
                    "arrival_date_week_number",
                    "arrival_date_day_of_month",
                    "stays_in_weekend_nights",
                    "stays_in_week_nights",
                    "adults",
                    "children",
                    "babies",
                    "meal",
                    "country",
                    "market_segment",
                    "distribution_channel",
                    "is_repeated_guest",
                    "previous_cancellations",
                    "previous_bookings_not_canceled",
                    "reserved_room_type",
                    "assigned_room_type",
                    "booking_changes",
                    "deposit_type",
                    "agent",
                    "company",
                    "days_in_waiting_list",
                    "customer_type",
                    "adr",
                    "required_car_parking_spaces",
                    "total_of_special_requests",
                    "reservation_status",
                    "reservation_status_date"
                order by "raw_booking_id"
            ) = 1,
            0, 1
        )::integer as is_duplicate,
        (
            coalesce(try_to_number(to_varchar("adults")), 0)
            + coalesce(try_to_number(to_varchar("children")), 0)
            + coalesce(try_to_number(to_varchar("babies")), 0)
        ) as guest_count,
        try_to_double(to_varchar("adr")) as raw_adr
    from source
),
cleaned as (
    select
        "raw_booking_id"::number(38,0) as raw_booking_id,
        trim("hotel") as hotel_name,
        try_to_number(to_varchar("is_canceled"))::integer as is_canceled,
        try_to_number(to_varchar("lead_time"))::integer as lead_time,

        to_date(
            to_varchar("arrival_date_year") || '-' ||
            lpad(
                case upper(trim("arrival_date_month"))
                    when 'JANUARY' then '1'
                    when 'FEBRUARY' then '2'
                    when 'MARCH' then '3'
                    when 'APRIL' then '4'
                    when 'MAY' then '5'
                    when 'JUNE' then '6'
                    when 'JULY' then '7'
                    when 'AUGUST' then '8'
                    when 'SEPTEMBER' then '9'
                    when 'OCTOBER' then '10'
                    when 'NOVEMBER' then '11'
                    when 'DECEMBER' then '12'
                end,
                2, '0'
            ) || '-' ||
            lpad(to_varchar("arrival_date_day_of_month"), 2, '0'),
            'YYYY-MM-DD'
        ) as arrival_date,

        try_to_number(to_varchar("arrival_date_week_number"))::integer as arrival_date_week_number,
        try_to_number(to_varchar("stays_in_weekend_nights"))::integer as stays_in_weekend_nights,
        try_to_number(to_varchar("stays_in_week_nights"))::integer as stays_in_week_nights,
        try_to_number(to_varchar("adults"))::integer as adults,
        coalesce(try_to_number(to_varchar("children")), 0)::integer as children,
        try_to_number(to_varchar("babies"))::integer as babies,

        trim("meal") as meal,
        trim("reserved_room_type") as reserved_room_type,
        trim("assigned_room_type") as assigned_room_type,
        trim("reservation_status") as reservation_status,

        try_to_number(to_varchar("booking_changes"))::integer as booking_changes,
        try_to_number(to_varchar("days_in_waiting_list"))::integer as days_in_waiting_list,
        try_to_number(to_varchar("required_car_parking_spaces"))::integer as required_car_parking_spaces,
        try_to_number(to_varchar("total_of_special_requests"))::integer as total_of_special_requests,

        round(raw_adr, 2) as _rounded_adr,
        iff(raw_adr < 0, 1, 0)::integer as adr_was_negative,
        greatest(round(raw_adr, 2), 0) as adr,
        to_date("reservation_status_date") as reservation_status_date,
        is_duplicate
    from marked
    where guest_count > 0
      and raw_adr >= 0
      and raw_adr <= {{ var('adr_max', 1000) }}
)
select
    raw_booking_id,
    hotel_name,
    is_canceled,
    lead_time,
    arrival_date,
    arrival_date_week_number,
    stays_in_weekend_nights,
    stays_in_week_nights,
    adults,
    children,
    babies,
    meal,
    reserved_room_type,
    assigned_room_type,
    booking_changes,
    days_in_waiting_list,
    adr,
    adr_was_negative,
    reservation_status,
    reservation_status_date,
    required_car_parking_spaces,
    total_of_special_requests,
    is_duplicate
from cleaned
