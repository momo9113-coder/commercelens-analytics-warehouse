-- KPI summary
SELECT
    COUNT(*) AS orders,
    SUM(order_value) AS gross_item_freight_value,
    AVG(late_delivery) AS late_delivery_rate,
    AVG(avg_review_score) AS average_review_score,
    AVG(delivery_days) AS average_delivery_days
FROM fct_orders;

-- Monthly operations trend
SELECT
    DATE_TRUNC('month', order_purchase_timestamp) AS month,
    COUNT(*) AS orders,
    SUM(order_value) AS gross_item_freight_value,
    AVG(late_delivery) AS late_delivery_rate,
    AVG(avg_review_score) AS average_review_score
FROM fct_orders
GROUP BY 1
ORDER BY 1;

-- Seller comparison, limited to sellers with enough orders
SELECT *
FROM fct_seller_performance
WHERE order_count >= 5
ORDER BY late_delivery_rate DESC, order_count DESC;

-- Delivery and review relationship
SELECT
    late_delivery,
    COUNT(*) AS orders,
    AVG(avg_review_score) AS average_review_score,
    AVG(order_value) AS average_order_value
FROM fct_orders
GROUP BY 1
ORDER BY 1;

-- State-level comparison
SELECT
    c.customer_state,
    COUNT(*) AS orders,
    AVG(f.late_delivery) AS late_delivery_rate,
    AVG(f.avg_review_score) AS average_review_score
FROM fct_orders f
JOIN stg_customers c USING (customer_id)
GROUP BY 1
ORDER BY orders DESC;
