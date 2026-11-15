
    
    

with child as (
    select lead_bucket_key as from_field
    from HOTEL_DWH.GOLD.fct_booking
    where lead_bucket_key is not null
),

parent as (
    select lead_bucket_key as to_field
    from HOTEL_DWH.GOLD.dim_lead_bucket
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


