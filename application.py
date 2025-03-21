import sqlite3
import pandas as pd
from utils import *
import json
db_path="olist.sqlite"

def create_connection(db_path):
    conn = sqlite3.connect(db_path)
    return conn


        

def get_sqlqueryfromllm(input_text,conn):
    try:
        if input_text is None:
            return None
        #if column_name is None:
        #    return None
        
        querystring= get_python_query_openai(input_text)
        print("Query String:",querystring)
        if querystring is None:
            return None
        else:
            data= json.loads(querystring)
            sql_query= data.get("query")            
            df = pd.read_sql_query(sql_query, conn)           
            columnnames= df.iloc[0].keys()           
            keycolumn= columnnames[0]            
            return df.iloc[0][keycolumn]

    except:
        return None
    
def get_sqlqueryfromllm_structuredoutput(input_text,conn):
    try:
        if input_text is None:
            return None
        #if column_name is None:
        #    return None
        
        querystring= get_python_query_openaistructuredOutput(input_text)
        print("Query String:",querystring)
        if querystring is None:
            return None
        else:
            #data= json.loads(querystring)
            #sql_query= data.get("query")         
            sql_query= querystring   
            df = pd.read_sql_query(sql_query, conn)           
            columnnames= df.iloc[0].keys()           
            keycolumn= columnnames[0]            
            return df.iloc[0][keycolumn]

    except:
        return None

    
    
def get_seller_with_most_orders_delivered_to_customers_in_rio(conn):  
    try:
        query = """
        SELECT sellers.seller_id, COUNT(DISTINCT orders.order_id) AS order_count
        FROM orders
        JOIN order_items ON orders.order_id = order_items.order_id
        JOIN sellers ON order_items.seller_id = sellers.seller_id
        JOIN customers ON orders.customer_id = customers.customer_id
        WHERE customers.customer_city = 'rio de janeiro' AND orders.order_status = 'delivered'
        GROUP BY sellers.seller_id
        ORDER BY order_count DESC
        LIMIT 1;
        """
        df = pd.read_sql_query(query, conn)    
        return df.iloc[0]['seller_id']
    except:
        return None
    

   

def get_average_reviewscore_for_beleza_saude_category(conn):
    try:
        query = """
        SELECT AVG(review_score) AS avg_review_score
        FROM order_reviews
        JOIN orders ON order_reviews.order_id = orders.order_id
        JOIN order_items ON orders.order_id = order_items.order_id
        JOIN products ON order_items.product_id = products.product_id
        WHERE products.product_category_name = 'beleza_saude';
        """
        df = pd.read_sql_query(query, conn)    
        return df.iloc[0]['avg_review_score']
    except:
        return None

def get_count_of_sellers_with_orders_more_than_100000BRL(conn):
    try:
        query = """
        SELECT COUNT(seller_id) AS seller_count
        FROM (
            SELECT sellers.seller_id, SUM(order_items.price) AS total_sales
            FROM order_items
            JOIN sellers ON order_items.seller_id = sellers.seller_id
            JOIN orders o ON order_items.order_id = o.order_id
            WHERE o.order_status = 'delivered'
            GROUP BY sellers.seller_id
            HAVING total_sales > 100000
        ) AS subquery;
        """
        df = pd.read_sql_query(query, conn)    
        return df.iloc[0]['seller_count']
    except:
        return None

    

def get_product_category_name_with_highest_5_star_review(conn):
    try:
        query = """
        SELECT 
        p.product_category_name
        FROM products p
        JOIN order_items oi ON p.product_id = oi.product_id
        JOIN order_reviews r ON oi.order_id = r.order_id
        GROUP BY p.product_category_name
        HAVING COUNT(*) > 100
        ORDER BY (COUNT(CASE WHEN r.review_score = 5 THEN 1 END) * 100.0 / COUNT(*)) DESC
        LIMIT 1
        """
        df = pd.read_sql_query(query, conn)   
        return df.iloc[0]['product_category_name']
    except:
        return None

def get_most_common_payment_installment_count_for_orders_over1000(conn):
    try:
        query = """
        SELECT payment_installments, COUNT(payment_installments) AS count
        FROM order_payments
        WHERE payment_value > 1000
        GROUP BY payment_installments
        ORDER BY count DESC
        LIMIT 1;
        """
        df = pd.read_sql_query(query, conn)    
        return df.iloc[0]['payment_installments']
    except:
        return None

def get_city_with_highest_average_freight_value_per_order(conn):
    try:
        query = """
        SELECT customers.customer_city,  AVG(freight_value) AS avg_freight_value
        FROM order_items
        JOIN orders ON order_items.order_id = orders.order_id
        JOIN customers ON orders.customer_id = customers.customer_id
        GROUP BY customer_city
        ORDER BY avg_freight_value DESC
        LIMIT 1;
        """
        df = pd.read_sql_query(query, conn)   
        return df.iloc[0]['customer_city'] 
    except:
        return None

def get_most_expensive_product_category_average_price(conn):
    try:
        query = """
        SELECT products.product_category_name, AVG(price) AS avg_price
        FROM order_items
        JOIN products ON order_items.product_id = products.product_id
        GROUP BY product_category_name
        ORDER BY avg_price DESC
        LIMIT 1;
        """
        df = pd.read_sql_query(query, conn)    
        return df.iloc[0]['product_category_name']
    except:
        return None
    
def getproductcategory_shortest_average_delivery_time(conn):
    try:
        query = """
        SELECT products.product_category_name, AVG(julianday(orders.order_delivered_customer_date) - julianday(orders.order_purchase_timestamp)) AS avg_delivery_time
        FROM orders
        JOIN order_items ON orders.order_id = order_items.order_id
        JOIN products ON order_items.product_id = products.product_id
        GROUP BY product_category_name
        ORDER BY avg_delivery_time ASC
        LIMIT 1;
        """
        df = pd.read_sql_query(query, conn)   
        return df.iloc[0]['product_category_name']
    except:
        return None

def get_orders_with_multiple_sellers(conn): 
    try:
        query = """
        SELECT COUNT(order_id) AS multi_seller_count
        FROM (
            SELECT order_id, COUNT(DISTINCT seller_id) AS seller_count
            FROM order_items
            GROUP BY order_id
            HAVING seller_count > 1
        ) AS subquery
        """
        df = pd.read_sql_query(query, conn)    
        return df.iloc[0]['multi_seller_count']
    except:
        return None

def getcountoforders_delivered_before_estimated_date(conn):
    try:
        query = """
        SELECT COUNT(order_id) AS early_delivery_count
        FROM (
            SELECT order_id, order_estimated_delivery_date, order_delivered_customer_date
            FROM orders
            WHERE order_delivered_customer_date < order_estimated_delivery_date 
            AND order_status = 'delivered'
        ) AS subquery
        """
        df = pd.read_sql_query(query, conn)    
        return df.iloc[0]['early_delivery_count']
    except:
        return None

def getcountoforders_delivered(conn):
    try:
        query = """
        SELECT COUNT(order_id) AS delivered_count
        FROM orders
        WHERE order_status = 'delivered'
        """
        df = pd.read_sql_query(query, conn)    
        return df.iloc[0]['delivered_count']
    except:
        return None

def calculate_percentageof_orders_delivered_before_estimated_date(conn):
    try:
        early_delivery_count = getcountoforders_delivered_before_estimated_date(conn)
        if early_delivery_count is None:
            return None
        delivered_count = getcountoforders_delivered(conn)
        if delivered_count is None:
            return None
        percentage = (early_delivery_count / delivered_count) * 100
        percentage = round(percentage, 2)
        return percentage
    except:
        return None

def main():
    conn = create_connection(db_path)
    #1
    result1= get_seller_with_most_orders_delivered_to_customers_in_rio(conn)
    result2= get_sqlqueryfromllm("Get the seller who has delivered the most orders to customers in Rio de Janeiro",conn)
    print("Seller with most sales in Rio de Janeiro:",result1)
    print("LLM output. Seller with most sales in Rio de Janeiro:",result2)
    print("Accuracy of Answer:",getaccuracypercentage(result1,result2))
    #2
    result1= get_count_of_sellers_with_orders_more_than_100000BRL(conn)
    result2= get_sqlqueryfromllm("How many sellers have completed orders worth more than 100000 in total",conn)
    print("How many sellers have completed orders worth more than 100000 BRL in total:",result1)
    print("LLM output. How many sellers have completed orders worth more than 100000 BRL in total:",result2)
    print("Accuracy of Answer:",getaccuracypercentage(result1,result2))
    

   
    
    conn.close()

if __name__ == "__main__":
    main()
