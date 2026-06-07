# for running open terminal: streamlit run ui_app.py
import streamlit as st
import sqlite3
import os
from dotenv import load_dotenv
from google import genai

# Load our hidden environment variables from the .env file
load_dotenv()

# We use Streamlit's cache session state so our database configuration runs smoothly
if 'db_configured' not in st.session_state:
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    cursor = connection.cursor()
    
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
    cursor.executemany("INSERT INTO products (product_name, price) VALUES (?, ?);", mock_products)
    connection.commit()
    
    # Store connections in session state so they persist across button clicks
    st.session_state.conn = connection
    st.session_state.cursor = cursor
    st.session_state.db_configured = True

# Helper function to talk to Gemini
def translate_text_to_sql_with_ai(user_input):
    try:
        client = genai.Client()
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
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        st.error(f"AI API Error: {e}")
        return None

# --- STREAMLIT UI LAYOUT ---
st.set_page_config(page_title="Text-to-SQL AI Engine", page_icon="🤖", layout="wide")

st.title("🤖 Natural Language to SQL Translator")
st.write("Type requests in plain English, and watch the AI generate and execute the SQL query in real-time!")

# Create two visual columns on the webpage
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💡 Ask the Database")
    english_command = st.text_input("Enter your command:", placeholder="e.g., Show me items cheaper than 100 dollars")
    
    if english_command:
        generated_sql = translate_text_to_sql_with_ai(english_command)
        
        if generated_sql:
            st.markdown("### 🖥️ Generated SQL Code:")
            st.code(generated_sql, language="sql")
            
            # Execute query against database
            try:
                st.session_state.cursor.execute(generated_sql)
                results = st.session_state.cursor.fetchall()
                
                with col2:
                    st.subheader("📊 Query Results")
                    if results:
                        # Display results in a clean interactive web table
                        st.dataframe(results, column_config={
                            "0": "Product ID",
                            "1": "Product Name",
                            "2": "Price ($)"
                        }, use_container_width=True)
                    else:
                        st.info("No records matched your query.")
            except sqlite3.OperationalError as sql_err:
                st.error(f"SQL Syntax Error: {sql_err}")

with col2:
    if not english_command:
        st.subheader("📋 Current Database Inventory")
        st.session_state.cursor.execute("SELECT * FROM products;")
        all_data = st.session_state.cursor.fetchall()
        st.dataframe(all_data, use_container_width=True)