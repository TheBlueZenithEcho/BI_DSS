
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select policy_key
from HOTEL_DWH.GOLD.dim_policy
where policy_key is null



  
  
      
    ) dbt_internal_test