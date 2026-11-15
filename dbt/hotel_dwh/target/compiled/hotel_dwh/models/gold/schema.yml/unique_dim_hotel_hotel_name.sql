
    
    

select
    hotel_name as unique_field,
    count(*) as n_records

from HOTEL_DWH.GOLD.dim_hotel
where hotel_name is not null
group by hotel_name
having count(*) > 1


