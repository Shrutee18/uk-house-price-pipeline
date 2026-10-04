WITH yearly AS (
    SELECT county, sale_year, COUNT(*) AS sales, MEDIAN(price) AS median_price
    FROM clean_ppd
    WHERE ppd_category_type = 'A'
    GROUP BY county, sale_year
    HAVING COUNT(*) >= 500
),
ranked AS (
    SELECT
        county, sale_year, sales, median_price,
        RANK() OVER (PARTITION BY sale_year ORDER BY median_price DESC) AS price_rank,
        COUNT(*) OVER (PARTITION BY sale_year) AS counties_ranked
    FROM yearly
)
SELECT county, sale_year, sales, ROUND(median_price) AS median_price,
       price_rank, counties_ranked
FROM ranked
WHERE county = 'GREATER MANCHESTER'
ORDER BY sale_year