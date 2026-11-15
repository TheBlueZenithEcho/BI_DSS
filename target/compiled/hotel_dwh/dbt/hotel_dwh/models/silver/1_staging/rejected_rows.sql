

-- Keep the original 32 source fields and the stable Bronze key.
-- Reason precedence matches the legacy Python assignment order:
-- adr_negative overrides adr_outlier, which overrides zero_guest.
with  __dbt__cte__stg_raw_hotel_bookings as (


-- Thin source wrapper. All Silver models read the same Bronze relation.
-- Do not generate or reorder raw_booking_id here.
select *
from HOTEL_DWH.BRONZE.raw_hotel_bookings
), source as (
    select *
    from __dbt__cte__stg_raw_hotel_bookings
),
classified as (
    select
        source.*,
        case
            when try_to_double(to_varchar("adr")) < 0 then 'adr_negative'
            when try_to_double(to_varchar("adr")) > 1000 then 'adr_outlier'
            when (
                coalesce(try_to_number(to_varchar("adults")), 0)
                + coalesce(try_to_number(to_varchar("children")), 0)
                + coalesce(try_to_number(to_varchar("babies")), 0)
            ) = 0 then 'zero_guest'
            else null
        end as reject_reason
    from source
)
select
    "raw_booking_id"::number(38,0) as raw_booking_id,
    reject_reason,
    "hotel" as hotel,
    "is_canceled" as is_canceled,
    "lead_time" as lead_time,
    "arrival_date_year" as arrival_date_year,
    "arrival_date_month" as arrival_date_month,
    "arrival_date_week_number" as arrival_date_week_number,
    "arrival_date_day_of_month" as arrival_date_day_of_month,
    "stays_in_weekend_nights" as stays_in_weekend_nights,
    "stays_in_week_nights" as stays_in_week_nights,
    "adults" as adults,
    "children" as children,
    "babies" as babies,
    "meal" as meal,
    "country" as country,
    "market_segment" as market_segment,
    "distribution_channel" as distribution_channel,
    "is_repeated_guest" as is_repeated_guest,
    "previous_cancellations" as previous_cancellations,
    "previous_bookings_not_canceled" as previous_bookings_not_canceled,
    "reserved_room_type" as reserved_room_type,
    "assigned_room_type" as assigned_room_type,
    "booking_changes" as booking_changes,
    "deposit_type" as deposit_type,
    "agent" as agent,
    "company" as company,
    "days_in_waiting_list" as days_in_waiting_list,
    "customer_type" as customer_type,
    "adr" as adr,
    "required_car_parking_spaces" as required_car_parking_spaces,
    "total_of_special_requests" as total_of_special_requests,
    "reservation_status" as reservation_status,
    "reservation_status_date" as reservation_status_date
from classified
where reject_reason is not null