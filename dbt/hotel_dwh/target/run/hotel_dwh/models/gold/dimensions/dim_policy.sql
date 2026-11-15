
  
    

create or replace transient table HOTEL_DWH.GOLD.dim_policy
    
    
    
    
    

    as (

-- Bảng tham số What-If: giữ nguyên 4 kịch bản Overbooking của legacy.
select
    policy_key,
    policy_name,
    ob_low_risk_pct,
    ob_medium_risk_pct,
    ob_high_risk_pct,
    7::integer as late_cancel_threshold_T,
    1.5::number(8,3) as compensation_multiplier
from values
    (1, 'Baseline (No OB)',   0.000, 0.000, 0.00),
    (2, 'Conservative 3%-8%', 0.030, 0.055, 0.08),
    (3, 'Moderate 5%-10%',    0.050, 0.075, 0.10),
    (4, 'Aggressive 8%-15%',  0.080, 0.115, 0.15)
as v(policy_key, policy_name, ob_low_risk_pct, ob_medium_risk_pct, ob_high_risk_pct)
    )
;


  