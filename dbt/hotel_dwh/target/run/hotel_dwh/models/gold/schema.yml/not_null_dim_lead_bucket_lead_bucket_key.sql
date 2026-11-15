
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select lead_bucket_key
from HOTEL_DWH.GOLD.dim_lead_bucket
where lead_bucket_key is null



  
  
      
    ) dbt_internal_test