CREATE OR REPLACE TABLE stg_orders AS
SELECT
    CAST(order_id AS VARCHAR) AS order_id,
    CAST(customer_id AS VARCHAR) AS customer_id,
    LOWER(TRIM(order_status)) AS order_status,
    TRY_CAST(order_purchase_timestamp AS TIMESTAMP) AS order_purchase_timestamp,
    TRY_CAST(order_approved_at AS TIMESTAMP) AS order_approved_at,
    TRY_CAST(order_delivered_carrier_date AS TIMESTAMP) AS order_delivered_carrier_date,
    TRY_CAST(order_delivered_customer_date AS TIMESTAMP) AS order_delivered_customer_date,
    TRY_CAST(order_estimated_delivery_date AS TIMESTAMP) AS order_estimated_delivery_date
FROM raw_orders;

CREATE OR REPLACE TABLE stg_order_items AS
SELECT
    CAST(order_id AS VARCHAR) AS order_id,
    CAST(order_item_id AS INTEGER) AS order_item_id,
    CAST(product_id AS VARCHAR) AS product_id,
    CAST(seller_id AS VARCHAR) AS seller_id,
    TRY_CAST(shipping_limit_date AS TIMESTAMP) AS shipping_limit_date,
    TRY_CAST(price AS DOUBLE) AS price,
    TRY_CAST(freight_value AS DOUBLE) AS freight_value
FROM raw_order_items;

CREATE OR REPLACE TABLE stg_payments AS
SELECT
    CAST(order_id AS VARCHAR) AS order_id,
    CAST(payment_sequential AS INTEGER) AS payment_sequential,
    LOWER(TRIM(payment_type)) AS payment_type,
    CAST(payment_installments AS INTEGER) AS payment_installments,
    TRY_CAST(payment_value AS DOUBLE) AS payment_value
FROM raw_payments;

CREATE OR REPLACE TABLE stg_reviews AS
SELECT
    CAST(review_id AS VARCHAR) AS review_id,
    CAST(order_id AS VARCHAR) AS order_id,
    CAST(review_score AS INTEGER) AS review_score,
    TRY_CAST(review_creation_date AS TIMESTAMP) AS review_creation_date,
    TRY_CAST(review_answer_timestamp AS TIMESTAMP) AS review_answer_timestamp
FROM raw_reviews;

CREATE OR REPLACE TABLE stg_customers AS
SELECT
    CAST(customer_id AS VARCHAR) AS customer_id,
    CAST(customer_unique_id AS VARCHAR) AS customer_unique_id,
    CAST(customer_zip_code_prefix AS INTEGER) AS customer_zip_code_prefix,
    LOWER(TRIM(customer_city)) AS customer_city,
    UPPER(TRIM(customer_state)) AS customer_state
FROM raw_customers;

CREATE OR REPLACE TABLE stg_products AS
SELECT
    CAST(product_id AS VARCHAR) AS product_id,
    NULLIF(LOWER(TRIM(product_category_name)), '') AS product_category_name,
    TRY_CAST(product_weight_g AS DOUBLE) AS product_weight_g,
    TRY_CAST(product_length_cm AS DOUBLE) AS product_length_cm,
    TRY_CAST(product_height_cm AS DOUBLE) AS product_height_cm,
    TRY_CAST(product_width_cm AS DOUBLE) AS product_width_cm
FROM raw_products;

CREATE OR REPLACE TABLE stg_sellers AS
SELECT
    CAST(seller_id AS VARCHAR) AS seller_id,
    CAST(seller_zip_code_prefix AS INTEGER) AS seller_zip_code_prefix,
    LOWER(TRIM(seller_city)) AS seller_city,
    UPPER(TRIM(seller_state)) AS seller_state
FROM raw_sellers;
