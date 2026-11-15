
    
    

select
    hotel_key as unique_field,
    count(*) as n_records

from HOTEL_DWH.GOLD.dim_hotel
where hotel_key is not null
group by hotel_key
having count(*) > 1


