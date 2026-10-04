# For running in terminal: python app.py
# For running in Streamlit: streamlit run app.py (or streamlit run ui_app.py)
import sqlite3
import os
import sys

# If launched via Streamlit ('streamlit run app.py'), delegate to ui_app.py
try:
    import streamlit as st
    if st.runtime.exists():
        ui_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui_app.py")
        if os.path.exists(ui_file):
            with open(ui_file, "r", encoding="utf-8") as f:
                exec(compile(f.read(), ui_file, 'exec'))
            raise SystemExit(0)
except SystemExit:
    raise
except Exception:
    pass

# Import the core universal SQL engine
from engine import universal_sql_engine, clean_input_text, parse_num

# ---------------------------------------------------------
# 1. Setup In-Memory Database (CLI / Library Mode)
# ---------------------------------------------------------
connection = sqlite3.connect(":memory:")
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

clean_input = clean_input_text


# ---------------------------------------------------------
# 2. Universal Natural Language to SQL Translator (100% Free)
# ---------------------------------------------------------
def translate_text_to_sql(user_input):
    """
    Universal NLP SQL Generator.
    Works for any user without API keys. Completely free, offline, and reliable.
    """
    return universal_sql_engine(user_input)


# ---------------------------------------------------------
# 3. CLI Test / Interactive
# ---------------------------------------------------------
if __name__ == "__main__":
    test_queries = [
        "want common data from tables products and customers",
        "who is the highest paid employee",
        "show all employees in engineering department",
        "list products with price less than 50 and category electronics",
        "orders created after 2023",
        "customers who have never ordered"
    ]
    print("\n=== Universal Text-to-SQL Engine Test ===")
    for q in test_queries:
        sql = translate_text_to_sql(q)
        print(f"'{q}' -> {sql}")
