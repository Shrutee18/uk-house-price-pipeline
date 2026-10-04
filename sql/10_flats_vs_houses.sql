WITH yearly AS (
    SELECT
        district,
        sale_year,
        CASE WHEN property_type = 'F' THEN 'Flat' ELSE 'House' END AS kind,
        COUNT(*) AS sales,
        MEDIAN(price) AS median_price
    FROM clean_ppd
    WHERE is_greater_manchester
      AND ppd_category_type = 'A'
      AND property_type != 'O'
    GROUP BY 1, 2, 3
),
ends AS (
    SELECT
        district,
        kind,
        SUM(sales) AS total_sales,
        MAX(CASE WHEN sale_year = 2018 THEN median_price END) AS m2018,
        MAX(CASE WHEN sale_year = 2025 THEN median_price END) AS m2025
    FROM yearly
    GROUP BY district, kind
)
SELECT
    district,
    kind,
    total_sales,
    ROUND(100.0 * total_sales / SUM(total_sales) OVER (PARTITION BY district), 1) AS share_of_sales_pct,
    ROUND(m2018) AS median_2018,
    ROUND(m2025) AS median_2025,
    ROUND(100.0 * (POWER(m2025 / m2018, 1.0 / 7) - 1), 2) AS cagr_pct
FROM ends
ORDER BY district, kind