-- KPI summary. A late-delivery flag is available only when both actual and
-- estimated delivery timestamps exist; AVG therefore uses the eligible denominator.
SELECT
    COUNT(*) AS orders,
    COUNT(*) FILTER (WHERE late_delivery IS NOT NULL) AS late_delivery_eligible_orders,
    SUM(order_value) AS gross_item_freight_value,
    AVG(late_delivery) AS late_delivery_rate,
    AVG(avg_review_score) AS average_review_score,
    AVG(delivery_days) AS average_delivery_days
FROM fct_orders;

-- Delivery/review association among reviewed orders with an eligible delivery flag.
SELECT
    late_delivery,
    COUNT(*) AS reviewed_orders,
    AVG(avg_review_score) AS average_review_score,
    AVG(CASE WHEN avg_review_score <= 2 THEN 1.0 ELSE 0.0 END) AS low_review_rate,
    AVG(delivery_days) AS average_delivery_days,
    AVG(order_value) AS average_order_value
FROM fct_orders
WHERE late_delivery IS NOT NULL
  AND avg_review_score IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- Monthly operations trend. Apply the report's >= 1,000-order threshold before
-- drawing conclusions so partial/low-volume edge months do not dominate.
SELECT
    DATE_TRUNC('month', order_purchase_timestamp) AS month,
    COUNT(*) AS eligible_orders,
    AVG(late_delivery) AS late_delivery_rate,
    AVG(avg_review_score) AS average_review_score
FROM fct_orders
WHERE late_delivery IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- State comparison. The public analysis interprets states with >= 1,000 eligible orders.
SELECT
    c.customer_state,
    COUNT(*) AS eligible_orders,
    AVG(f.late_delivery) AS late_delivery_rate,
    AVG(f.avg_review_score) AS average_review_score,
    AVG(f.delivery_days) AS average_delivery_days
FROM fct_orders f
JOIN stg_customers c USING (customer_id)
WHERE f.late_delivery IS NOT NULL
GROUP BY 1
ORDER BY eligible_orders DESC, customer_state;

-- Seller reliability distribution for sellers with >= 100 eligible orders.
WITH order_sellers AS (
    SELECT DISTINCT order_id, seller_id
    FROM stg_order_items
), seller AS (
    SELECT
        os.seller_id,
        COUNT(*) AS eligible_orders,
        AVG(f.late_delivery) AS late_delivery_rate,
        AVG(f.avg_review_score) AS average_review_score
    FROM order_sellers os
    JOIN fct_orders f USING (order_id)
    WHERE f.late_delivery IS NOT NULL
    GROUP BY 1
    HAVING COUNT(*) >= 100
)
SELECT
    COUNT(*) AS eligible_sellers,
    MIN(late_delivery_rate) AS min_late_delivery_rate,
    MEDIAN(late_delivery_rate) AS median_late_delivery_rate,
    QUANTILE_CONT(late_delivery_rate, 0.9) AS p90_late_delivery_rate,
    MAX(late_delivery_rate) AS max_late_delivery_rate,
    CORR(late_delivery_rate, average_review_score) AS late_review_correlation
FROM seller;
