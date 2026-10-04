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
    SELECT area, sale_year, MEDIAN(price) AS median_price
    FROM grouped
    GROUP BY area, sale_year
),
real AS (
    SELECT
        y.area,
        y.sale_year,
        y.median_price,
        y.median_price * (SELECT cpi FROM cpi_annual WHERE year = 2025) / c.cpi AS real_median_2025_prices
    FROM yearly y
    JOIN cpi_annual c ON c.year = y.sale_year
)
SELECT
    area,
    sale_year,
    ROUND(median_price) AS nominal_median,
    ROUND(real_median_2025_prices) AS real_median_2025_prices,
    ROUND(100.0 * real_median_2025_prices /
          FIRST_VALUE(real_median_2025_prices) OVER (PARTITION BY area ORDER BY sale_year), 1)
        AS real_price_index_2018
FROM real
ORDER BY area, sale_year
