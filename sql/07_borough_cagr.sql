WITH yearly AS (
    SELECT district, sale_year, MEDIAN(price) AS median_price
    FROM clean_ppd
    WHERE is_greater_manchester AND ppd_category_type = 'A'
    GROUP BY district, sale_year
),
ends AS (
    SELECT
        district,
        MAX(CASE WHEN sale_year = 2018 THEN median_price END) AS median_2018,
        MAX(CASE WHEN sale_year = 2025 THEN median_price END) AS median_2025
    FROM yearly
    GROUP BY district
)
SELECT
    district,
    ROUND(median_2018) AS median_2018,
    ROUND(median_2025) AS median_2025,
    ROUND(100.0 * (median_2025 / median_2018 - 1), 1) AS total_growth_pct,
    ROUND(100.0 * (POWER(median_2025 / median_2018, 1.0 / 7) - 1), 2) AS cagr_pct
FROM ends
ORDER BY cagr_pct DESC