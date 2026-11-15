
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    bucket_label as unique_field,
    count(*) as n_records

from HOTEL_DWH.GOLD.dim_lead_bucket
where bucket_label is not null
group by bucket_label
having count(*) > 1



  
  
      
    ) dbt_internal_test