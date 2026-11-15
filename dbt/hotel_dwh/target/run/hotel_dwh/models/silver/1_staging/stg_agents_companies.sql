
  
    

create or replace transient table HOTEL_DWH.SILVER.stg_agents_companies
    
    
    
    
    

    as (

with  __dbt__cte__stg_raw_hotel_bookings as (


-- Thin source wrapper. All Silver models read the same Bronze relation.
-- Do not generate or reorder raw_booking_id here.
select *
from HOTEL_DWH.BRONZE.raw_hotel_bookings
), casted as (
    select
        "raw_booking_id"::number(38,0) as raw_booking_id,
        coalesce(try_to_number(to_varchar("agent")), 0)::integer as agent_id,
        coalesce(try_to_number(to_varchar("company")), 0)::integer as company_id
    from __dbt__cte__stg_raw_hotel_bookings
)
select
    raw_booking_id,
    agent_id,
    company_id,
    iff(company_id > 0, 1, 0)::integer as has_company
from casted
    )
;


  