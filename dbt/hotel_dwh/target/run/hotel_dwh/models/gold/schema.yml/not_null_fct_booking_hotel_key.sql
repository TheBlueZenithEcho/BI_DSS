
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select hotel_key
from HOTEL_DWH.GOLD.fct_booking
where hotel_key is null



  
  
      
    ) dbt_internal_test