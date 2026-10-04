WITH grouped AS (
    SELECT
        sale_year,
        CASE WHEN is_greater_manchester THEN 'Greater Manchester'
             WHEN county = 'GREATER LONDON' THEN 'Greater London'
             ELSE 'Rest of England and Wales' END AS area,
        price
    FROM clean_ppd
    WHERE ppd_category_type = 'A'
),
yearly AS (
    SELECT area, sale_year, COUNT(*) AS sales, MEDIAN(price) AS median_price
    FROM grouped
    GROUP BY area, sale_year
)
SELECT
    area,
    sale_year,
    sales,
    ROUND(median_price) AS median_price,
    ROUND(100.0 * median_price /
          FIRST_VALUE(median_price) OVER (PARTITION BY area ORDER BY sale_year), 1) AS price_index_2018
FROM yearly
ORDER BY area, sale_year