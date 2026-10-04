WITH yearly AS (
    SELECT district, sale_year, MEDIAN(price) AS median_price
    FROM clean_ppd
    WHERE is_greater_manchester AND ppd_category_type = 'A'
    GROUP BY district, sale_year
),
ends AS (
    SELECT
        district,
        MAX(CASE WHEN sale_year = 2018 THEN median_price END) AS m2018,
        MAX(CASE WHEN sale_year = 2025 THEN median_price END) AS m2025
    FROM yearly
    GROUP BY district
),
cpi AS (
    SELECT
        MAX(CASE WHEN year = 2018 THEN cpi END) AS cpi2018,
        MAX(CASE WHEN year = 2025 THEN cpi END) AS cpi2025
    FROM cpi_annual
)
SELECT
    district,
    ROUND(100.0 * (m2025 / m2018 - 1), 1) AS nominal_growth_pct,
    ROUND(100.0 * ((m2025 / m2018) / (cpi2025 / cpi2018) - 1), 1) AS real_growth_pct,
    ROUND(100.0 * (POWER((m2025 / m2018) / (cpi2025 / cpi2018), 1.0 / 7) - 1), 2) AS real_cagr_pct
FROM ends, cpi
ORDER BY real_cagr_pct DESC