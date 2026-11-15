
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select hotel_name
from HOTEL_DWH.GOLD.dim_hotel
where hotel_name is null



  
  
      
    ) dbt_internal_test