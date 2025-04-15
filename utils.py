from openai import OpenAI
from openai import AzureOpenAI
import os
import json

from dotenv import load_dotenv
from pydantic import BaseModel, Field
import pandas as pd
import csv

# Load environment variables from .env file
load_dotenv(dotenv_path="/Users/priyanka.raghavan/Documents/llmassignment/llm_assignment_priyanka/myenv.env")

# Access environment variables
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
openai_api_key = os.getenv("AZURE_OPEN_AI_API_KEY")
azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
azure_openai_model = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# Define our structured output format
class SQLGeneration(BaseModel):
    reasoning: list[str] = Field(..., description="Short reasoning steps explaining the approach")
    sql_query: str = Field(..., description="The final SQL query (PostgreSQL syntax)")

user_question = "Which product category has the highest rate of 5-star reviews?"


def get_python_query_openaistructuredOutput(input_text):
    systemprompt= create_prompt()
    try:    
        if validate_input_text(input_text) is False:
            print("Invalid input!!!")
            return None
        # Create a conversation with few-shot examples
        messages = [
        {"role": "system", "content": f"{systemprompt}"},
        {"role": "user", "content": "Which seller has delivered the most orders to customers in Rio de Janeiro?"}, 
        {"role": "assistant", "content": "SELECT s.seller_id, COUNT(*) AS order_count FROM orders o JOIN customers c ON o.customer_id = c.customer_id JOIN sellers s ON o.seller_id = s.seller_id WHERE c.customer_city = 'rio de janeiro' AND o.order_status = 'delivered' GROUP BY s.seller_id ORDER BY order_count DESC LIMIT 1;"},
        {"role": "user", "content": "What's the average review score for 'beleza_saude' products?"},
        {"role": "assistant", "content": "SELECT AVG(r.review_score) AS avg_score FROM order_reviews r JOIN order_items oi ON r.order_id = oi.order_id JOIN products p ON oi.product_id = p.product_id WHERE p.product_category_name = 'beleza_saude';"},
        {"role": "user", "content": f"{input_text}"}
        ]       
        client = AzureOpenAI(
        azure_endpoint=azure_endpoint,
        api_key=openai_api_key,
        api_version=azure_openai_api_version
        )
        response = client.beta.chat.completions.parse(
            model="gpt-4o 2024-08-06",
            messages=messages,
            response_format=SQLGeneration
        )
        result= response.choices[0].message.parsed
        result1= response.choices[0].message.parsed.sql_query
        #print("Sql query results:",result1)
        #print("Parsed results:",result)
        #print(response.model_dump_json(indent=2))
        return result1
        
    except Exception as e:
        print(e)
        return None

def removestringsfromjsonoutput(modeloutput,replacestring):
    model_output= modeloutput.replace(replacestring,"")
    return model_output

def clean_up_outoput(model_output):   
    try:
        # Attempt to parse the message content as JSON
        parsed_content = json.loads(model_output)
        # If successful, handle the content as a JSON object
        # (You can access keys and values as needed)    
        return model_output
    except json.JSONDecodeError:
        # If parsing fails, treat the content as a plain string        
        if "```json" in model_output:
            model_output= removestringsfromjsonoutput(model_output,"```json")
            if "```" in model_output:
              model_output= removestringsfromjsonoutput(model_output,"```")
              parsed_content = model_output              
              return parsed_content
        if "```" in model_output:
            model_output= removestringsfromjsonoutput(model_output,"```")
            parsed_content = model_output           
            return parsed_content
        return None

def get_python_query_openai(input_text):
    systemprompt= create_prompt_basic()
    try:    
        if validate_input_text(input_text) is False:
            print("Invalid input!!!")
            return None
        #client = OpenAI(api_key=openai_api_key)
        client = AzureOpenAI(
        azure_endpoint=azure_endpoint,
        api_key=openai_api_key,
        api_version=azure_openai_api_version
        )
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
        
        return clean_up_outoput(response.choices[0].message.content)
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
    
def create_prompt_basic():
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

def create_prompt():
    prompt= f"""
            YYou are an expert in SQLite, Python and data analysis.
You work at Invoice Processing Department analyzing global shipping invoices.
Given a user request, respond with a json string that returns a query string required to run task.
Limit output only to 1 amswer and no not give multiple answers.
The data is from https://www.kaggle.com/datasets/terencicp/e-commerce-dataset-by-olist-as-an-sqlite-database/data

The output should be as follows
"""+ "\n\n"+ """
{
    "query": "SELECT sellers.seller_id, COUNT(orders.order_id) AS order_count FROM orders JOIN order_items ON orders.order_id = order_items.order_id JOIN sellers ON order_items.seller_id = sellers.seller_id JOIN customers ON orders.customer_id = customers.customer_id WHERE customers.customer_city = 'rio de janeiro' AND orders.order_status = 'delivered' GROUP BY sellers.seller_id ORDER BY order_count DESC LIMIT 1;",
    
}


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
    This is a Brazilian e-commerce dataset from Olist Store with the following characteristics:

    - **orders**: Contains ~99.4k order records. 97% are 'delivered' status, with others including 'shipped', 'canceled', etc. Timestamps track the order journey from purchase to delivery.
    - **order_items**: Contains ~113k records. Each order can have multiple items, with price and freight values for each item.
    - **order_payments**: Contains ~104k records. 74% of payments are by credit card, 19% by 'boleto', with installment options ranging from 1-24.
    - **customers**: Contains ~99.4k records. Major cities include São Paulo (16%) and Rio de Janeiro (7%), with SP being the most common state (42%).
    - **sellers**: Contains ~3k records. Primarily located in São Paulo (22%) and Curitiba (4%), with SP being the most common state (60%).
    - **products**: Contains ~33k records. Top categories include 'cama_mesa_banho' (9%) and 'esporte_lazer' (9%).
    - **order_reviews**: Contains review scores from 1-5, with comments and timestamps.
    - **geolocation**: Contains geographic coordinates for Brazilian ZIP codes.

    ## Key Relationships and Data Notes

    1. Customers and sellers are linked via zip code prefixes to geolocation.
    2. The `order_items` table shows how to calculate order totals (item price + freight).
    3. Multiple payment methods may appear for a single order.
    4. Product categories are in Portuguese (e.g., 'beleza_saude' = health & beauty).
    5. Some records contain unusual values (e.g., 'Infinity' for customer_unique_id).
    6. Date fields sometimes contain '01/01/0001 00:00:00' as placeholder.
    7. Orders can have multiple items from different sellers.

    ## Example Questions and Answers

        Question: Which seller has delivered the most orders to customers in Rio de Janeiro? [string: seller_id]
        ```sql
        SELECT 
            s.seller_id
        FROM sellers s
        JOIN order_items oi ON s.seller_id = oi.seller_id
        JOIN orders o ON oi.order_id = o.order_id
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE c.customer_city = 'rio de janeiro'
            AND o.order_status = 'delivered'
        GROUP BY s.seller_id
        ORDER BY COUNT(DISTINCT o.order_id) DESC
        LIMIT 1;
        ```

        Question: What's the average review score for products in the 'beleza_saude' category? [float: score]
        ```sql
        SELECT 
            ROUND(AVG(r.review_score), 2) as avg_score
        FROM products p
        JOIN order_items oi ON p.product_id = oi.product_id
        JOIN order_reviews r ON oi.order_id = r.order_id
        WHERE p.product_category_name = 'beleza_saude';
        ```

        Question: How many sellers have completed orders worth more than 100,000 BRL in total? [integer: count]
        ```sql
        SELECT COUNT(*) as seller_count
        FROM (
            SELECT s.seller_id
            FROM sellers s
            JOIN order_items oi ON s.seller_id = oi.seller_id
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.order_status = 'delivered'
            GROUP BY s.seller_id
            HAVING SUM(oi.price) > 100000
        ) high_value_sellers;
        ```



    """ +"\n\n"+ """
```
"""
    return prompt


listofallowedQuestions= [
    "Which seller has delivered the most orders to customers in customer city 'rio de janeiro'",
    "Get the seller who has delivered the most orders to customers in rio de janeiro?[string: seller_id]",
    "How many sellers have completed orders worth more than 100,000 BRL in total? [integer: count]",
    "What's the average review score for products in the 'beleza_saude' category? [float: score]",
    "Which product category has the highest rate of 5-star reviews? [string: category_name]",
    "What's the most common payment installment count for orders over 1000 BRL? [integer: installments]",
    "Which city has the highest average freight value per order? [string: city_name]",
    "What's the most expensive product category based on average price? [string: category_name]",
    "Which product category has the shortest average delivery time? [string: category_name]",
    "How many orders have items from multiple sellers?",
    "How many orders have items from multiple sellers? [integer: count]",
    "What percentage of orders are delivered before the estimated delivery date? [float: percentage]"
    "Get the percentage of orders delivered before estimated delivery date",
    "Which seller has delivered the most orders to customers in rio de janeiro?",
    "What's the average review score for products in the 'beleza_saude' category?",
    "How many sellers have completed orders worth more than 100000 in total?",
    "Which product category has the highest rate of 5-star reviews?",
    "Get the most common payment installment count for orders over 1000",
    "What's the most common payment installment count for orders over 1000 BRL?",
    "Which city has the highest average freight value per order?",
    "What's the most expensive product category based on average price?",
    "Which product category has the shortest average delivery time?",    
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


def getsummaryfromresumedatacsv():
    try:        
        second_column_data = extract_second_column('resume/resumedata.csv')
        if second_column_data:
            print("Second Column Data:")
        #for data in second_column_data[:5]:  # Print first 5 rows for brevity
        #    print(data)
        return second_column_data
    except Exception as e:
        print(e)
        return None

def extract_all_manualchecklistintolist(file_path):
    try:
        data_list = []
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row
            for row in reader:
                data_list.append(row)  
        return data_list
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None

def extract_second_column(file_path):
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row
            second_column_data = [row[1] for row in reader if len(row) > 1]
        return second_column_data
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None
def getcountofskills(skillchecklist):
    try:
        if skillchecklist is None:
            return 0
        if len(skillchecklist)<=0:
            return 0
        count=0
        for skill in skillchecklist:
            count+=1
        return count
    except Exception as e:
        print(e)
        return 0  
    
def percentagesimilaritysummaryssameaschecklist(summary,checklist):
    try:

        if summary is None or checklist is None:
            return 0
        if len(summary)<=0 or len(checklist)<=0:
            return 0
        count=getcountofskills(checklist)
        countsummary=0
        for skill in summary:
            skilllowercase= skill.replace(" ", "").lower()
            for check in checklist:                
                checklowercase= check.replace(" ", "").lower()
                if skilllowercase == checklowercase or skilllowercase in checklowercase or checklowercase in skilllowercase:
                    countsummary += 1
                    break
        if countsummary==count:
            return 100
        else:
            if count==0:
                return 0
            else:
                return countsummary/count*100
            
    except Exception as e:
        print(e)
        return 0
def percentagesimilaritysummaryssameaschecklistSTR(summary,checklist):
    try:

        if summary is None or checklist is None:
            return 0
        lowercase_summary = summary.replace(" ", "").lower()
        lowercase_checklist = checklist.replace(" ", "").lower()
        if lowercase_summary== lowercase_checklist or lowercase_summary in lowercase_checklist or lowercase_checklist in lowercase_summary:
            return 100
        else:
            return 0
    except Exception as e:
        print(e)
        return 0
def percentagesimilaritysummaryssameaschecklistINT(summary,checklist):
    try:

        if summary is None or checklist is None:
            return 0
        if summary== checklist:
            return 100
        else:
            return 0
    except Exception as e:
        print(e)
        return 0
    

