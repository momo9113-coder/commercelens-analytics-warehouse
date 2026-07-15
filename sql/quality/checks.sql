-- Each query should return zero failing rows/counts.
SELECT 'duplicate_order_ids' AS check_name, COUNT(*) AS failures
FROM (SELECT order_id FROM stg_orders GROUP BY order_id HAVING COUNT(*) > 1);

SELECT 'orphan_order_items' AS check_name, COUNT(*) AS failures
FROM stg_order_items i
LEFT JOIN stg_orders o USING (order_id)
WHERE o.order_id IS NULL;

SELECT 'orphan_reviews' AS check_name, COUNT(*) AS failures
FROM stg_reviews r
LEFT JOIN stg_orders o USING (order_id)
WHERE o.order_id IS NULL;

SELECT 'negative_item_amounts' AS check_name, COUNT(*) AS failures
FROM stg_order_items
WHERE price < 0 OR freight_value < 0;

SELECT 'invalid_order_status' AS check_name, COUNT(*) AS failures
FROM stg_orders
WHERE order_status NOT IN ('delivered', 'shipped', 'canceled', 'invoiced', 'processing', 'unavailable', 'approved', 'created');

SELECT 'delivery_before_purchase' AS check_name, COUNT(*) AS failures
FROM stg_orders
WHERE order_delivered_customer_date < order_purchase_timestamp;

SELECT 'duplicate_fct_orders' AS check_name, COUNT(*) AS failures
FROM (SELECT order_id FROM fct_orders GROUP BY order_id HAVING COUNT(*) > 1);

SELECT 'invalid_review_score' AS check_name, COUNT(*) AS failures
FROM stg_reviews
WHERE review_score IS NOT NULL AND (review_score < 1 OR review_score > 5);
