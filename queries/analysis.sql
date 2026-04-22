-- =============================================
-- CreditPulse SA — Analytical Queries
-- Author: Tisetso Letuka
-- Description: Core queries powering Act 1 analysis
-- =============================================

-- Query 1: Impaired consumers over time
SELECT 
    d.period_label,
    d.year,
    d.quarter,
    d.month,
    f.category,
    f.value_millions
FROM fact_consumer_standing f
JOIN dim_period d ON f.period_id = d.period_id
WHERE f.category = 'Impaired records (#)'
ORDER BY d.year, d.month;

-- Query 2:  Impairment rate (impaired as % of credit-active consumers):

SELECT 
    d.period_label,
    d.year,
    d.month,
    MAX(CASE WHEN f.category = 'Impaired records (#)' THEN f.value_millions END) as impaired,
    MAX(CASE WHEN f.category = 'Credit-active consumers (#)' THEN f.value_millions END) as credit_active,
    ROUND(
        MAX(CASE WHEN f.category = 'Impaired records (#)' THEN f.value_millions END) /
        MAX(CASE WHEN f.category = 'Credit-active consumers (#)' THEN f.value_millions END) * 100
    , 2) as impairment_rate_pct
FROM fact_consumer_standing f
JOIN dim_period d ON f.period_id = d.period_id
GROUP BY d.period_id, d.period_label, d.year, d.month
ORDER BY d.year, d.month;
