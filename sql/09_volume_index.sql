WITH yearly AS (
    SELECT
        sale_year,
        CASE WHEN is_greater_manchester THEN 'Greater Manchester'
             ELSE 'Rest of England and Wales' END AS area,
        COUNT(*) AS sales
    FROM clean_ppd
    WHERE ppd_category_type = 'A'
    GROUP BY 1, 2
)
SELECT
    area,
    sale_year,
    sales,
    ROUND(100.0 * sales / FIRST_VALUE(sales) OVER (PARTITION BY area ORDER BY sale_year), 1) AS volume_index_2018
FROM yearly
ORDER BY area, sale_year