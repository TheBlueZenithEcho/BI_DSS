
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select booking_id
from HOTEL_DWH.GOLD.fct_booking
where booking_id is null



  
  
      
    ) dbt_internal_test