
    
    

select
    policy_key as unique_field,
    count(*) as n_records

from HOTEL_DWH.GOLD.dim_policy
where policy_key is not null
group by policy_key
having count(*) > 1


