
  
    

create or replace transient table HOTEL_DWH.GOLD.dim_lead_bucket
    
    
    
    
    

    as (

-- Giữ nguyên 6 khoảng lead-time cố định từ common.LEAD_BUCKETS.
select *
from values
    (1, '0-7d',     0,    7),
    (2, '8-30d',    8,   30),
    (3, '31-90d',  31,   90),
    (4, '91-180d', 91,  180),
    (5, '181-365d',181, 365),
    (6, '>365d',  366, 9999)
as v(lead_bucket_key, bucket_label, min_days, max_days)
    )
;


  