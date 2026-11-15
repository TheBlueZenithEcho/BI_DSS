
    
    

select
    booking_id as unique_field,
    count(*) as n_records

from HOTEL_DWH.GOLD.fct_booking
where booking_id is not null
group by booking_id
having count(*) > 1


