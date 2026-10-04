SELECT
    sale_year,
    sale_month,
    COUNT(*) AS sales,
    ROUND(100.0 * COUNT(*) / AVG(COUNT(*)) OVER (PARTITION BY sale_year), 1) AS sales_index,
    ROUND(MEDIAN(price)) AS median_price
FROM clean_ppd
WHERE ppd_category_type = 'A'
  AND is_greater_manchester
GROUP BY sale_year, sale_month
ORDER BY sale_year, sale_month