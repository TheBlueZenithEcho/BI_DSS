
  
    

create or replace transient table HOTEL_DWH.GOLD.dim_hotel
    
    
    
    
    

    as (

-- Giữ surrogate key cố định: City Hotel = 1, Resort Hotel = 2.
-- Sức chứa là giả định nghiệp vụ được giữ nguyên từ common.py.
select
    case hotel_name
        when 'City Hotel' then 1
        when 'Resort Hotel' then 2
    end::integer as hotel_key,
    hotel_name,
    replace(hotel_name, ' Hotel', '') as hotel_type,
    case hotel_name
        when 'City Hotel' then 216
        when 'Resort Hotel' then 184
    end::integer as capacity_dedup,
    case hotel_name
        when 'City Hotel' then 226
        when 'Resort Hotel' then 187
    end::integer as capacity_all
from HOTEL_DWH.SILVER.stg_hotels
where hotel_name in ('City Hotel', 'Resort Hotel')
    )
;


  