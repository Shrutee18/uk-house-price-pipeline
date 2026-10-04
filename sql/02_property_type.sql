SELECT
    property_type_label,
    CASE WHEN is_greater_manchester THEN 'Greater Manchester'
         ELSE 'Rest of England and Wales' END AS area,
    COUNT(*) AS sales,
    ROUND(MEDIAN(price)) AS median_price
FROM clean_ppd
WHERE ppd_category_type = 'A'
  AND property_type != 'O'
GROUP BY 1, 2
ORDER BY 1, 2