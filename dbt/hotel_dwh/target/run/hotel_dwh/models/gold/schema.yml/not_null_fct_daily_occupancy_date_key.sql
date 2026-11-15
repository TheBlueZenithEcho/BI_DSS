
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select date_key
from HOTEL_DWH.GOLD.fct_daily_occupancy
where date_key is null



  
  
      
    ) dbt_internal_test