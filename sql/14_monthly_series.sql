SELECT
    sale_month_start AS month_start,
    COUNT(*) AS sales,
    MEDIAN(price) AS median_price
FROM clean_ppd
WHERE is_greater_manchester
  AND ppd_category_type = 'A'
GROUP BY sale_month_start
ORDER BY sale_month_start