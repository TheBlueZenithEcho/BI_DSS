

-- Grain = 1 dòng / booking hợp lệ trong int_booking_risk.
-- Không loại duplicate: giữ is_duplicate để dashboard có thể chọn S1 (0) hoặc S0 (tất cả).
-- Các dimension join phải là 1:1; không được làm thay đổi số dòng fact.
with bookings as (
    select *
    from HOTEL_DWH.SILVER.int_booking_risk
),
joined as (
    select
        b.*,
        h.hotel_key,
        s.segment_key,
        lb.lead_bucket_key,
        to_number(to_char(b.arrival_date, 'YYYYMMDD'))::number(8,0) as arrival_date_key,
        to_number(to_char(b.booking_date, 'YYYYMMDD'))::number(8,0) as booking_date_key,
        to_number(to_char(b.departure_date, 'YYYYMMDD'))::number(8,0) as departure_date_key
    from bookings b
    left join HOTEL_DWH.GOLD.dim_hotel h
        on b.hotel_name = h.hotel_name
    left join HOTEL_DWH.GOLD.dim_segment s
        on b.market_segment = s.market_segment
       and b.distribution_channel = s.distribution_channel
       and b.deposit_type = s.deposit_type
       and b.customer_type = s.customer_type
    left join HOTEL_DWH.GOLD.dim_lead_bucket lb
        on b.lead_bucket = lb.bucket_label
)
select
    raw_booking_id as booking_id,
    hotel_key,
    segment_key,
    lead_bucket_key,
    arrival_date_key,
    booking_date_key,
    departure_date_key,
    lead_time,
    stays_in_weekend_nights,
    stays_in_week_nights,
    total_nights,
    adults,
    children,
    babies,
    adr,
    potential_revenue,
    realized_revenue,
    revenue_at_risk,
    booking_changes,
    days_in_waiting_list,
    previous_cancellations,
    previous_bookings_not_canceled,
    is_canceled,
    is_no_show,
    is_late_cancel,
    is_early_cancel,
    is_eligible_at_T,
    cancel_notice_days,
    round(p_late_group, 6) as p_late_group,
    risk_group,
    is_room_changed,
    is_zero_night,
    is_zero_adr,
    is_duplicate
from joined