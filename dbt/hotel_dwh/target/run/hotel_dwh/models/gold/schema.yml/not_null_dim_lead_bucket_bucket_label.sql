
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select bucket_label
from HOTEL_DWH.GOLD.dim_lead_bucket
where bucket_label is null



  
  
      
    ) dbt_internal_test