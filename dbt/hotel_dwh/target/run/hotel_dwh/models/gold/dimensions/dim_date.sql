
  
    

create or replace transient table HOTEL_DWH.GOLD.dim_date
    
    
    
    
    

    as (

-- Giữ logic legacy: lịch liên tục từ booking_date nhỏ nhất
-- đến departure_date lớn nhất trong int_booking_risk.
with date_bounds as (
    select
        min(booking_date)::date as min_date,
        max(departure_date)::date as max_date
    from HOTEL_DWH.SILVER.int_booking_risk
),
day_offsets as (
    select row_number() over (order by seq4()) - 1 as day_offset
    from table(generator(rowcount => 10000))
),
date_spine as (
    select dateadd(day, n.day_offset, b.min_date)::date as full_date
    from date_bounds b
    cross join day_offsets n
    where n.day_offset <= datediff(day, b.min_date, b.max_date)
)
select
    to_number(to_char(full_date, 'YYYYMMDD'))::number(8,0) as date_key,
    full_date,
    day(full_date)::integer as day,
    trim(to_char(full_date, 'DAY')) as day_name,
    weekiso(full_date)::integer as iso_week,
    month(full_date)::integer as month,
    trim(to_char(full_date, 'MONTH')) as month_name,
    quarter(full_date)::integer as quarter,
    year(full_date)::integer as year,
    to_char(full_date, 'YYYY-MM') as year_month,
    iff(dayofweekiso(full_date) in (6, 7), 1, 0)::integer as is_weekend
from date_spine
    )
;


  