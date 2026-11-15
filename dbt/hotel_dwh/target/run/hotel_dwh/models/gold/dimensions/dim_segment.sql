
  
    

create or replace transient table HOTEL_DWH.GOLD.dim_segment
    
    
    
    
    

    as (

-- Junk dimension: một dòng cho mỗi tổ hợp duy nhất
-- market_segment x distribution_channel x deposit_type x customer_type.
with distinct_segments as (
    select distinct
        market_segment,
        distribution_channel,
        deposit_type,
        customer_type
    from HOTEL_DWH.SILVER.stg_segments
)
select
    row_number() over (
        order by market_segment, distribution_channel, deposit_type, customer_type
    )::integer as segment_key,
    market_segment,
    distribution_channel,
    deposit_type,
    customer_type
from distinct_segments
    )
;


  