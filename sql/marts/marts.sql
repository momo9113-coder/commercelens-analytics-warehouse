CREATE OR REPLACE TABLE fct_orders AS
WITH item_rollup AS (
    SELECT
        order_id,
        COUNT(*) AS item_count,
        SUM(COALESCE(price, 0) + COALESCE(freight_value, 0)) AS order_value,
        COUNT(DISTINCT seller_id) AS seller_count
    FROM stg_order_items
    GROUP BY order_id
), review_rollup AS (
    SELECT
        order_id,
        AVG(review_score) AS avg_review_score,
        COUNT(*) AS review_count
    FROM stg_reviews
    GROUP BY order_id
)
SELECT
    o.order_id,
    o.customer_id,
    o.order_status,
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    COALESCE(i.item_count, 0) AS item_count,
    COALESCE(i.order_value, 0) AS order_value,
    COALESCE(i.seller_count, 0) AS seller_count,
    r.avg_review_score,
    COALESCE(r.review_count, 0) AS review_count,
    CASE
        WHEN o.order_delivered_customer_date IS NOT NULL
         AND o.order_estimated_delivery_date IS NOT NULL
         AND o.order_delivered_customer_date > o.order_estimated_delivery_date
        THEN 1 ELSE 0
    END AS late_delivery,
    CASE
        WHEN o.order_purchase_timestamp IS NOT NULL
         AND o.order_delivered_customer_date IS NOT NULL
        THEN DATE_DIFF('day', o.order_purchase_timestamp, o.order_delivered_customer_date)
        ELSE NULL
    END AS delivery_days
FROM stg_orders o
LEFT JOIN item_rollup i USING (order_id)
LEFT JOIN review_rollup r USING (order_id);

CREATE OR REPLACE TABLE fct_seller_performance AS
WITH order_sellers AS (
    SELECT DISTINCT order_id, seller_id
    FROM stg_order_items
)
SELECT
    os.seller_id,
    COUNT(*) AS order_count,
    SUM(f.order_value / NULLIF(f.seller_count, 0)) AS allocated_gmv,
    AVG(f.late_delivery) AS late_delivery_rate,
    AVG(f.avg_review_score) AS average_review_score
FROM order_sellers os
JOIN fct_orders f USING (order_id)
GROUP BY os.seller_id;
