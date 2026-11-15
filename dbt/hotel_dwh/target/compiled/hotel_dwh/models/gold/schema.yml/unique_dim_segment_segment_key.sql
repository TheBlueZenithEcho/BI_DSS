
    
    

select
    segment_key as unique_field,
    count(*) as n_records

from HOTEL_DWH.GOLD.dim_segment
where segment_key is not null
group by segment_key
having count(*) > 1


