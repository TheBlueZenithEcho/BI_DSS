
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    lead_bucket_key as unique_field,
    count(*) as n_records

from HOTEL_DWH.GOLD.dim_lead_bucket
where lead_bucket_key is not null
group by lead_bucket_key
having count(*) > 1



  
  
      
    ) dbt_internal_test