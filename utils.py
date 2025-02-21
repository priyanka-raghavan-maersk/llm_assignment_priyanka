
from openai import OpenAI
import os



openai_api_key = os.getenv("OPEN_AI_API_KEY")
def get_python_query_openai(input_text):
    systemprompt= create_prompt()
    try:    
        if validate_input_text(input_text) is False:
            print("Invalid input!!!")
            return None
        client = OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": systemprompt
                },
                {
                    "role": "user",
                    "content": input_text
                }
            ],
            temperature=1,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        #print("response:",response.choices[0].message.content)
        return response.choices[0].message.content
    except Exception as e:
        print(e)
        return None
    
def get_python_query_openai_checksimilarity(input_text, column_name):
    
    try:        
        client = OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant who can let the user know if the input text is similar to the second input text. If answer is mostly similar reply True else reply false"
                },
                {
                    "role": "user",
                    "content": "Is the input text similar to the second input text?"+ "\n\n"+ "Input text: "+ input_text + "\n\n"+ "Second input text: "+ column_name
                }
            ],
            temperature=1,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )        
        return response.choices[0].message.content
    except Exception as e:
        print(e)
        return None
    

def create_prompt():
    prompt= f"""
            You are an expert in SQLite, Python and data analysis.
You work at Invoice Processing Department analyzing global shipping invoices.
Given a user request, respond with a json string that returns a query string required to run task.
Limit output only to 1 amswer and no not give multiple answers.
The data is from https://www.kaggle.com/datasets/terencicp/e-commerce-dataset-by-olist-as-an-sqlite-database/data

The output should be as follows
"""+ "\n\n"+ """
{
    "query": "SELECT sellers.seller_id, COUNT(orders.order_id) AS order_count FROM orders JOIN order_items ON orders.order_id = order_items.order_id JOIN sellers ON order_items.seller_id = sellers.seller_id JOIN customers ON orders.customer_id = customers.customer_id WHERE customers.customer_city = 'rio de janeiro' AND orders.order_status = 'delivered' GROUP BY sellers.seller_id ORDER BY order_count DESC LIMIT 1;",
    
}

Tables in this SQLite database:


// Some [Exploratory Data Analysis](https://en.wikipedia.org/wiki/Exploratory_data_analysis) can be added as well to improve quality of queries

A few important conventions:
1. All monetary values are in USD cents
2. All dates are in UTC timezone
3. For tables - return DataFrame, for reports - return markdown

Tables inSQLite database
-Customers 99441 rows and 5 column
-geolocation 1000163 rows and 5 columns
-order_items 112650 rows and 7 columns
-order_payments 103886 and 5 columns
- order_reviews 99224 rows and 7 columns
-orders 99441 rows and 8 columns
-products 32951 rows and 8 columns


Database schema is attached below. 

```mermaid
""" +"\n\n"+ """
erDiagram
    orders ||--o{ order_items : contains
    orders ||--o{ order_payments : has
    orders ||--o{ order_reviews : has
    orders }|--|| customers : placed_by
    order_items }|--|| products : includes
    order_items }|--|| sellers : sold_by
    sellers }|--|| geolocation : located_in
    customers }|--|| geolocation : located_in

    orders {
        string order_id
        string customer_id
        string order_status
        datetime order_purchase_timestamp
        datetime order_approved_at
        datetime order_delivered_carrier_date
        datetime order_delivered_customer_date
        datetime order_estimated_delivery_date
    }

    order_items {
        string order_id
        int order_item_id
        string product_id
        string seller_id
        datetime shipping_limit_date
        float price
        float freight_value
    }

    order_payments {
        string order_id
        int payment_sequential
        string payment_type
        int payment_installments
        float payment_value
    }

    order_reviews {
        string review_id
        string order_id
        int review_score
        string review_comment_title
        string review_comment_message
        datetime review_creation_date
        datetime review_answer_timestamp
    }

    customers {
        string customer_id
        string customer_unique_id
        string customer_zip_code_prefix
        string customer_city
        string customer_state
    }

    sellers {
        string seller_id
        string seller_zip_code_prefix
        string seller_city
        string seller_state
    }

    products {
        string product_id
        string product_category_name
        int product_name_length
        int product_description_length
        int product_photos_qty
        float product_weight_g
        float product_length_cm
        float product_height_cm
        float product_width_cm
    }

    geolocation {
        string geolocation_zip_code_prefix
        float geolocation_lat
        float geolocation_lng
        string geolocation_city
        string geolocation_state
    }
    """ +"\n\n"+ """
```
"""
    return prompt


listofallowedQuestions= [
    "Get the seller who has delivered the most orders to customers in Rio de Janeiro",
    "How many sellers have completed orders worth more than 100,000 BRL in total",
    "Get the average review score for 'beleza_saude' category",
    "Get the product category with highest 5 star reviews",
    "Get the most common payment installment count for orders over 1000",
    "Get the city with highest average freight value per order",
    "Get the most expensive product category average price",
    "Get the product category with shortest average delivery time",
    "How many orders have items with multiple sellers",
    "Get the percentage of orders delivered before estimated delivery date",
    "Which seller has delivered the most orders to customers in Rio de Janeiro?",
    "What's the average review score for products in the 'beleza_saude' category?",
    "How many sellers have completed orders worth more than 100,000 BRL in total?",
    "Which product category has the highest rate of 5-star reviews?",
    "What's the most common payment installment count for orders over 1000 BRL?",
    "Which city has the highest average freight value per order?",
    "What's the most expensive product category based on average price?",
    "Which product category has the shortest average delivery time?",
    "How many orders have items from multiple sellers?",
    "What percentage of orders are delivered before the estimated delivery date?"]





def validate_input_text(input_text):
    try:
        if input_text is None:
            return False
        if len(input_text)<=0:
            return False
        for question in listofallowedQuestions:
            if question.lower() == input_text.lower():
                return True
        
        return False
    except Exception as e:
        print(e)
        return False
    
def getaccuracypercentage(sqlqueryans,llmqueryans):
    try:
        difference= abs(sqlqueryans-llmqueryans)
        accuracy= 100- (difference / sqlqueryans * 100)
        return max(0, accuracy)
    except Exception as e:
        print(e)
        return 0


