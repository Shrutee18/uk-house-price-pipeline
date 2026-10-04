SELECT
    county,
    COUNT(*) AS sales,
    ROUND(MEDIAN(price)) AS median_price,
    RANK() OVER (ORDER BY MEDIAN(price) DESC) AS price_rank
FROM clean_ppd
WHERE ppd_category_type = 'A'
GROUP BY county
HAVING COUNT(*) >= 1000
ORDER BY median_price DESC
