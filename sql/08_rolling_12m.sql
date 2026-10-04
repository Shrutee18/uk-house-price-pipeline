WITH months AS (
    SELECT DISTINCT sale_month_start AS month_start
    FROM clean_ppd
    WHERE is_greater_manchester
),
gm AS (
    SELECT sale_month_start, price
    FROM clean_ppd
    WHERE is_greater_manchester AND ppd_category_type = 'A'
)
SELECT
    m.month_start,
    COUNT(*) AS sales_in_window,
    ROUND(MEDIAN(g.price)) AS rolling_12m_median
FROM months m
JOIN gm g
  ON g.sale_month_start > m.month_start - INTERVAL 12 MONTH
 AND g.sale_month_start <= m.month_start
GROUP BY m.month_start
HAVING COUNT(DISTINCT g.sale_month_start) = 12
ORDER BY m.month_start