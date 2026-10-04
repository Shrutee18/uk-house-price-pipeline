WITH yearly AS (
    SELECT
        district,
        sale_year,
        COUNT(*) AS sales,
        MEDIAN(price) AS median_price
    FROM clean_ppd
    WHERE is_greater_manchester
      AND ppd_category_type = 'A'
    GROUP BY district, sale_year
),
growth AS (
    SELECT
        district,
        sale_year,
        sales,
        median_price,
        LAG(median_price) OVER (PARTITION BY district ORDER BY sale_year) AS prev_median
    FROM yearly
)
SELECT
    district,
    sale_year,
    sales,
    ROUND(median_price) AS median_price,
    ROUND(prev_median) AS prev_year_median,
    ROUND(100.0 * (median_price - prev_median) / prev_median, 1) AS yoy_growth_pct
FROM growth
WHERE prev_median IS NOT NULL
ORDER BY sale_year DESC, yoy_growth_pct DESC