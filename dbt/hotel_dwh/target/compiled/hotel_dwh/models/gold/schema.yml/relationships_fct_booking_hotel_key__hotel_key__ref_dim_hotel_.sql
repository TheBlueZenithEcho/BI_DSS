
    
    

with child as (
    select hotel_key as from_field
    from HOTEL_DWH.GOLD.fct_booking
    where hotel_key is not null
),

parent as (
    select hotel_key as to_field
    from HOTEL_DWH.GOLD.dim_hotel
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


