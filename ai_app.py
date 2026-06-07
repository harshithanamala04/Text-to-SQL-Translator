# for running open terminal python app.py
# sqlite is a python inbuilt library
import sqlite3
import os
from dotenv import load_dotenv
from google import genai

# Load our hidden environment variables from the .env file
load_dotenv()

# 1. Setup our In-Memory Database
connection = sqlite3.connect(":memory:")
cursor = connection.cursor()
# cursor helps in running the query line by line

cursor.execute("""
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    price REAL NOT NULL
);
""")

mock_products = [
    ('Laptop', 999.99), 
    ('Earphones', 29.99), 
    ('Phone', 699.99),
    ('Smartwatch', 199.50),
    ('Tablet', 450.00),
    ('Keyboard', 49.99),
    ('Monitor', 249.99)
    ]
cursor.execute("DELETE FROM products;") # Clean old data and re-insert the larger dataset
cursor.executemany("INSERT INTO products (product_name, price) VALUES (?, ?);", mock_products)
connection.commit()


# 2. Our New LLM-Based Translator Function
def translate_text_to_sql_with_ai(user_input):
    try:
        # Initialize the Gemini client (it automatically looks for GEMINI_API_KEY in your .env)
        client = genai.Client()
        
        # Crafting a clear prompt telling the AI exactly what our database looks like
        prompt = f"""
        You are an expert system that translates English into pure SQLite code.
        Given the following database schema:
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            price REAL NOT NULL
        );
        
        Translate this English command into a valid SQLite query: "{user_input}"
        
        CRITICAL: Return ONLY the raw SQL code. Do not include markdown blocks, backticks, or any conversational text.
        """
        
        # Call the Gemini 2.5 Flash model
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        # Clean up the response just in case the AI added extra spaces or a trailing semicolon mismatch
        generated_sql = response.text.strip()
        return generated_sql

    except Exception as e:
        print(f"An error occurred while connecting to the AI API: {e}")
        return None


    # 4. Run the AI's generated SQL against our database
print("\n=== AI Text-to-SQL Translator Engine ===")
print("Type your question in plain English (e.g., 'Show me items under 100 dollars')")
print("Type 'exit' to quit the application.\n")

while True:
    english_command = input("Ask the Database: ")
    
    # Check if the user wants to break out of the loop
    if english_command.lower() == 'exit':
        print("Goodbye!")
        break
        
    if not english_command.strip():
        continue
        
    # Get the SQL translation from Gemini
    generated_sql = translate_text_to_sql_with_ai(english_command)
    
    if generated_sql:
        print(f"Generated SQL:  {generated_sql}")
        
        # Run it against the database using our try-except block
        try:
            cursor.execute(generated_sql)
            results = cursor.fetchall()
            print(f"Database Results: {results}\n")
        except sqlite3.OperationalError as sql_err:
            print(f"❌ The AI generated invalid SQL syntax: {sql_err}\n")