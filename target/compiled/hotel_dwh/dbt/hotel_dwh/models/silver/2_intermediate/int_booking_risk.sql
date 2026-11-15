

-- Intermediate model: join the four row-level staging tables and reproduce
-- the legacy feature engineering and fallback risk-estimation algorithm.



with bookings as (
    select * from HOTEL_DWH.SILVER.stg_bookings
),
segments as (
    select * from HOTEL_DWH.SILVER.stg_segments
),
customers as (
    select * from HOTEL_DWH.SILVER.stg_customers
),
agents_companies as (
    select * from HOTEL_DWH.SILVER.stg_agents_companies
),
joined as (
    select
        b.*,
        s.market_segment,
        s.distribution_channel,
        s.deposit_type,
        s.customer_type,
        c.country,
        c.is_repeated_guest,
        c.previous_cancellations,
        c.previous_bookings_not_canceled,
        a.agent_id,
        a.company_id,
        a.has_company
    from bookings b
    inner join segments s using (raw_booking_id)
    inner join customers c using (raw_booking_id)
    inner join agents_companies a using (raw_booking_id)
),
time_features as (
    select
        *,
        stays_in_weekend_nights + stays_in_week_nights as total_nights,
        dateadd(day, -lead_time, arrival_date)::date as booking_date,
        dateadd(
            day,
            stays_in_weekend_nights + stays_in_week_nights,
            arrival_date
        )::date as departure_date,
        datediff(day, reservation_status_date, arrival_date) as _notice_days
    from joined
),
cancel_features as (
    select
        *,
        iff(is_canceled = 1, _notice_days, null)::integer as cancel_notice_days,
        iff(reservation_status = 'No-Show', 1, 0)::integer as is_no_show,
        iff(
            (is_canceled = 1 and coalesce(_notice_days, 1000000) <= 7)
            or reservation_status = 'No-Show',
            1, 0
        )::integer as is_late_cancel,
        iff(
            is_canceled = 1
            and coalesce(_notice_days, 1000000) > 7
            and reservation_status <> 'No-Show',
            1, 0
        )::integer as is_early_cancel,
        iff(
            lead_time >= 7
            and (
                is_canceled = 0
                or coalesce(_notice_days, 1000000) <= 7
            ),
            1, 0
        )::integer as is_eligible_at_T,
        case
            when lead_time between 0 and 7 then '0-7d'
            when lead_time between 8 and 30 then '8-30d'
            when lead_time between 31 and 90 then '31-90d'
            when lead_time between 91 and 180 then '91-180d'
            when lead_time between 181 and 365 then '181-365d'
            when lead_time > 365 then '>365d'
            else null
        end as lead_bucket
    from time_features
),
dedup_base as (
    select *
    from cancel_features
    where is_duplicate = 0
),
l1 as (
    select
        hotel_name, market_segment, distribution_channel, deposit_type, lead_bucket,
        sum(is_eligible_at_T) as n_eligible,
        sum(is_late_cancel * is_eligible_at_T) as n_late,
        sum(is_late_cancel * is_eligible_at_T) / nullif(sum(is_eligible_at_T), 0) as p
    from dedup_base
    group by hotel_name, market_segment, distribution_channel, deposit_type, lead_bucket
),
l2 as (
    select
        hotel_name, market_segment, deposit_type, lead_bucket,
        sum(is_eligible_at_T) as n_eligible,
        sum(is_late_cancel * is_eligible_at_T) as n_late,
        sum(is_late_cancel * is_eligible_at_T) / nullif(sum(is_eligible_at_T), 0) as p
    from dedup_base
    group by hotel_name, market_segment, deposit_type, lead_bucket
),
l3 as (
    select
        hotel_name, lead_bucket,
        sum(is_eligible_at_T) as n_eligible,
        sum(is_late_cancel * is_eligible_at_T) as n_late,
        sum(is_late_cancel * is_eligible_at_T) / nullif(sum(is_eligible_at_T), 0) as p
    from dedup_base
    group by hotel_name, lead_bucket
),
l4 as (
    select
        hotel_name,
        sum(is_eligible_at_T) as n_eligible,
        sum(is_late_cancel * is_eligible_at_T) as n_late,
        sum(is_late_cancel * is_eligible_at_T) / nullif(sum(is_eligible_at_T), 0) as p
    from dedup_base
    group by hotel_name
),
with_probabilities as (
    select
        d.*,
        case
            when l1.n_eligible >= 300 then l1.p
            when l2.n_eligible >= 300 then l2.p
            when l3.n_eligible >= 300 then l3.p
            else l4.p
        end as p_late_group,
        case
            when l1.n_eligible >= 300 then 'L1_group'
            when l2.n_eligible >= 300 then 'L2_seg_deposit_bucket'
            when l3.n_eligible >= 300 then 'L3_hotel_bucket'
            else 'L4_hotel'
        end as p_late_source
    from cancel_features d
    left join l1
      on d.hotel_name = l1.hotel_name
     and d.market_segment = l1.market_segment
     and d.distribution_channel = l1.distribution_channel
     and d.deposit_type = l1.deposit_type
     and d.lead_bucket = l1.lead_bucket
    left join l2
      on d.hotel_name = l2.hotel_name
     and d.market_segment = l2.market_segment
     and d.deposit_type = l2.deposit_type
     and d.lead_bucket = l2.lead_bucket
    left join l3
      on d.hotel_name = l3.hotel_name
     and d.lead_bucket = l3.lead_bucket
    left join l4
      on d.hotel_name = l4.hotel_name
),
rounded_probabilities as (
    select
        *,
        round(p_late_group, 6) as p_late_group_rounded
    from with_probabilities
),
risk_distribution as (
    select
        hotel_name,
        p_late_group_rounded as p_late_group,
        count(*) as n_bookings
    from rounded_probabilities
    where is_duplicate = 0
    group by hotel_name, p_late_group_rounded
),
risk_midpoints as (
    select
        hotel_name,
        p_late_group,
        (
            sum(n_bookings) over (
                partition by hotel_name
                order by p_late_group
                rows between unbounded preceding and current row
            ) - n_bookings / 2.0
        ) / nullif(sum(n_bookings) over (partition by hotel_name), 0) as cumulative_midpoint
    from risk_distribution
),
risk_labels as (
    select
        hotel_name,
        p_late_group,
        case
            when cumulative_midpoint <= 1.0 / 3.0 then 'Low'
            when cumulative_midpoint <= 2.0 / 3.0 then 'Medium'
            else 'High'
        end as risk_group
    from risk_midpoints
),
final as (
    select
        p.*,
        r.risk_group,
        round(adr * total_nights, 2) as potential_revenue,
        iff(is_canceled = 0, round(adr * total_nights, 2), 0)::number(18,2) as realized_revenue,
        iff(
            is_late_cancel = 1 or is_no_show = 1,
            round(adr * total_nights, 2),
            0
        )::number(18,2) as revenue_at_risk,
        iff(reserved_room_type <> assigned_room_type, 1, 0)::integer as is_room_changed,
        iff(total_nights = 0, 1, 0)::integer as is_zero_night,
        iff(adr = 0, 1, 0)::integer as is_zero_adr
    from rounded_probabilities p
    left join risk_labels r
      on p.hotel_name = r.hotel_name
     and p.p_late_group_rounded = r.p_late_group
)
select
    * exclude (_notice_days, p_late_group_rounded)
from final