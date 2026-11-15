
    
    

with child as (
    select segment_key as from_field
    from HOTEL_DWH.GOLD.fct_booking
    where segment_key is not null
),

parent as (
    select segment_key as to_field
    from HOTEL_DWH.GOLD.dim_segment
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


