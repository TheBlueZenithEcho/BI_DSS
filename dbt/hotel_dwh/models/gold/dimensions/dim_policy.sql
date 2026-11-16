
{{ config(materialized='table') }}
with policies as (
    select
        policy_key,
        policy_code,
        policy_name,
        policy_type,
        hotel_scope,
        ob_low_risk_pct,
        ob_medium_risk_pct,
        ob_high_risk_pct
    from values
        (1, 'P0', 'No overbooking',                     'BASELINE',        'ALL',          0.000, 0.000, 0.000),
        (2, 'P1', 'Uniform 5%',                         'UNIFORM',         'ALL',          0.050, 0.050, 0.050),
        (3, 'P2', 'Uniform 8%',                         'UNIFORM',         'ALL',          0.080, 0.080, 0.080),
        (4, 'P3', 'Uniform 15%',                        'UNIFORM',         'ALL',          0.150, 0.150, 0.150),
        (5, 'P4', 'Task scenario 8% / 11.5% / 15%',     'TASK_SCENARIO',   'ALL',          0.080, 0.115, 0.150),
        (6, 'P5', 'Optimal uniform 6% (City)',          'OPTIMAL_UNIFORM', 'City Hotel',   0.060, 0.060, 0.060),
        (7, 'P5', 'Optimal uniform 3% (Resort)',        'OPTIMAL_UNIFORM', 'Resort Hotel', 0.030, 0.030, 0.030),
        (8, 'P6', 'Optimal risk-based 4/6/13% (City)',  'OPTIMAL_RISK',    'City Hotel',   0.040, 0.060, 0.130),
        (9, 'P6', 'Optimal risk-based 2/3/9% (Resort)', 'OPTIMAL_RISK',    'Resort Hotel', 0.020, 0.030, 0.090)
    as v(
        policy_key,
        policy_code,
        policy_name,
        policy_type,
        hotel_scope,
        ob_low_risk_pct,
        ob_medium_risk_pct,
        ob_high_risk_pct
    )
)

select
    policy_key::integer as policy_key,
    policy_code::varchar as policy_code,
    policy_name::varchar as policy_name,
    policy_type::varchar as policy_type,
    hotel_scope::varchar as hotel_scope,
    ob_low_risk_pct::number(8,3) as ob_low_risk_pct,
    ob_medium_risk_pct::number(8,3) as ob_medium_risk_pct,
    ob_high_risk_pct::number(8,3) as ob_high_risk_pct,
    {{ var('late_cancel_t', 7) }}::integer as late_cancel_threshold_T,
    {{ var('compensation_multiplier', 1.5) }}::number(8,3) as compensation_multiplier
from policies
