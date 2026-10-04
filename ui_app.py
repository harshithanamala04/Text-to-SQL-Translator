# Streamlit Real-Time Text-to-SQL Translation Engine
# Run command: streamlit run ui_app.py
import streamlit as st
import sqlite3
import pandas as pd
import time
import os
import re
import warnings
from dotenv import load_dotenv

# Suppress warnings
warnings.filterwarnings("ignore")

# Load environment variables if available
load_dotenv()

# Flexible Gemini client import if available
GEMINI_SDK_TYPE = None
try:
    from google import genai
    GEMINI_SDK_TYPE = "genai"
except ImportError:
    try:
        import google.generativeai as legacy_genai
        GEMINI_SDK_TYPE = "legacy"
    except ImportError:
        GEMINI_SDK_TYPE = None

# ---------------------------------------------------------
# 1. STREAMLIT PAGE CONFIG & CLEAN STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="English to SQL Translator",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
        max-width: 1050px;
    }
    .hero-container {
        text-align: center;
        margin-bottom: 22px;
    }
    .hero-title {
        font-size: 2.3rem;
        font-weight: 700;
        margin-bottom: 6px;
        color: var(--text-color, #1e293b);
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #64748b;
        margin: 0;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(16, 185, 129, 0.12);
        color: #059669;
        font-size: 0.82rem;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 20px;
        margin-top: 10px;
    }
    .pulse-dot {
        width: 7px;
        height: 7px;
        background: #10b981;
        border-radius: 50%;
    }
    .card-title {
        font-size: 1.15rem;
        font-weight: 600;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    /* Spacious SQL Query Box - No scrolling needed */
    div[data-testid="stCodeBlock"] {
        width: 100% !important;
        margin-bottom: 12px !important;
    }
    div[data-testid="stCodeBlock"] pre {
        white-space: pre-wrap !important;
        word-break: break-word !important;
        overflow-x: visible !important;
        font-size: 1.05rem !important;
        line-height: 1.6 !important;
        padding: 16px 20px !important;
        border-radius: 10px !important;
    }
    div[data-testid="stCodeBlock"] code {
        white-space: pre-wrap !important;
        word-break: break-word !important;
        font-size: 1.05rem !important;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# 2. IN-MEMORY DATABASE SETUP & SESSION STATE
# ---------------------------------------------------------
def initialize_database():
    """Initializes in-memory SQLite database and seeds default tables."""
    if 'db_configured' not in st.session_state:
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        cursor = conn.cursor()
        
        # 1. products
        cursor.execute("""
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            price REAL NOT NULL
        );
        """)
        mock_products = [
            (1, 'Laptop', 999.99), 
            (2, 'Earphones', 29.99), 
            (3, 'Phone', 699.99),
            (4, 'Smartwatch', 199.50),
            (5, 'Tablet', 450.00),
            (6, 'Keyboard', 49.99),
            (7, 'Monitor', 249.99)
        ]
        cursor.executemany("INSERT INTO products (product_id, product_name, price) VALUES (?, ?, ?);", mock_products)
        
        # 2. customers
        cursor.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            city TEXT NOT NULL,
            total_spent REAL NOT NULL,
            product_id INTEGER
        );
        """)
        mock_customers = [
            (1, 'Alice Smith', 'London', 1029.98, 1),
            (2, 'Bob Jones', 'New York', 49.99, 6),
            (3, 'Charlie Brown', 'London', 699.99, 3),
            (4, 'Diana Prince', 'Paris', 249.99, 7)
        ]
        cursor.executemany("INSERT INTO customers (customer_id, customer_name, city, total_spent, product_id) VALUES (?, ?, ?, ?, ?);", mock_customers)

        # 3. orders
        cursor.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            order_date TEXT NOT NULL
        );
        """)
        mock_orders = [
            (101, 1, 1, 999.99, '2026-01-15'),
            (102, 1, 2, 29.99, '2026-02-10'),
            (103, 2, 6, 49.99, '2026-02-18'),
            (104, 3, 3, 699.99, '2026-03-01')
        ]
        cursor.executemany("INSERT INTO orders (order_id, customer_id, product_id, total_amount, order_date) VALUES (?, ?, ?, ?, ?);", mock_orders)

        # 4. employees
        cursor.execute("""
        CREATE TABLE employees (
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name TEXT NOT NULL,
            department TEXT NOT NULL,
            salary REAL NOT NULL,
            hire_date TEXT NOT NULL
        );
        """)
        mock_employees = [
            (1, 'John Doe', 'Engineering', 85000, '2021-06-15'),
            (2, 'Jane Miller', 'Sales', 62000, '2022-03-10'),
            (3, 'Sam Wilson', 'Marketing', 58000, '2023-01-20'),
            (4, 'Emily Clark', 'Engineering', 92000, '2020-11-05')
        ]
        cursor.executemany("INSERT INTO employees (employee_id, employee_name, department, salary, hire_date) VALUES (?, ?, ?, ?, ?);", mock_employees)
        
        conn.commit()
        st.session_state.conn = conn
        st.session_state.cursor = cursor
        st.session_state.db_configured = True

# Initialize state variables
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'current_prompt' not in st.session_state:
    st.session_state.current_prompt = "Show me items cheaper than 100 dollars"
if 'current_sql' not in st.session_state:
    st.session_state.current_sql = ""
if 'current_results' not in st.session_state:
    st.session_state.current_results = None
if 'current_columns' not in st.session_state:
    st.session_state.current_columns = []
if 'current_latency_ms' not in st.session_state:
    st.session_state.current_latency_ms = 0.0
if 'current_engine' not in st.session_state:
    st.session_state.current_engine = "Universal Free SQL Engine"
if 'current_error' not in st.session_state:
    st.session_state.current_error = None
if 'user_query_input' not in st.session_state:
    st.session_state.user_query_input = "Show me items cheaper than 100 dollars"
if 'last_executed_prompt' not in st.session_state:
    st.session_state.last_executed_prompt = ""

initialize_database()


# ---------------------------------------------------------
# 3. UNIVERSAL NATURAL LANGUAGE TO SQL CONVERTER (100% FREE)
# ---------------------------------------------------------
from engine import universal_sql_engine, explain_sql, clean_input_text, parse_num


# ---------------------------------------------------------
# 4. OPTIONAL GEMINI CLIENT (TRANSPARENT PASS-THROUGH)
# ---------------------------------------------------------
def translate_with_gemini(user_input, api_key):
    """Cloud AI translator when a Gemini key is provided."""
    if not api_key or not GEMINI_SDK_TYPE:
        return None
    prompt = f"""
    You are an expert SQL Generator. Your sole task is to convert natural language questions into valid, clean, and optimized ANSI SQL / SQLite queries.
    Standard database schema:
    - products (product_id, product_name, price)
    - customers (customer_id, customer_name, city, total_spent, product_id)
    - orders (order_id, customer_id, product_id, total_amount, order_date)
    - employees (employee_id, employee_name, department, salary, hire_date)
    If the question references other entities (e.g., students, flights, movies), make standard logical ANSI SQL schema assumptions.
    
    Question: "{user_input}"
    
    CRITICAL: Return ONLY raw SQL code ending with a semicolon. Do NOT include markdown code blocks, backticks, or conversational text.
    """
    try:
        if GEMINI_SDK_TYPE == "genai":
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            sql = response.text.strip()
        else:
            legacy_genai.configure(api_key=api_key)
            model = legacy_genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            sql = response.text.strip()

        if sql.startswith("```"):
            sql = sql.strip("`")
            if sql.lower().startswith("sql"):
                sql = sql[3:].strip()
        sql = sql.strip()
        if not sql.endswith(";"):
            sql += ";"
        return sql
    except Exception:
        return None


# ---------------------------------------------------------
# 5. CORE REACTIVE PIPELINE
# ---------------------------------------------------------
def execute_query_pipeline(prompt_text):
    """Translates text to SQL, runs against database, and updates session state."""
    if not prompt_text or not prompt_text.strip():
        return

    start_time = time.perf_counter()
    sql_query = None

    # Step 1: Check for Gemini API key (from session state or environment)
    active_key = st.session_state.get("gemini_key_input", "").strip() or os.getenv("GEMINI_API_KEY", "").strip()
    if active_key:
        sql_query = translate_with_gemini(prompt_text, active_key)

    # Step 2: High-Precision Universal Engine (100% Free, zero keys required)
    if not sql_query:
        sql_query = universal_sql_engine(prompt_text)

    # Step 3: Run against SQLite database if query targets local tables
    results = []
    cols = []
    if sql_query:
        try:
            if any(t in sql_query.lower() for t in ["products", "customers", "orders", "employees"]):
                st.session_state.cursor.execute(sql_query)
                results = st.session_state.cursor.fetchall()
                if st.session_state.cursor.description:
                    cols = [d[0] for d in st.session_state.cursor.description]
            st.session_state.current_error = None
        except sqlite3.OperationalError:
            # Table or join on external schema assumption - ignore execution errors
            pass

    end_time = time.perf_counter()
    latency_ms = round((end_time - start_time) * 1000, 2)

    # Step 4: Update reactive session state
    st.session_state.current_prompt = prompt_text
    st.session_state.current_sql = sql_query or ""
    st.session_state.current_results = results
    st.session_state.current_columns = cols
    st.session_state.current_latency_ms = latency_ms
    st.session_state.last_executed_prompt = prompt_text

    # Record into history
    if sql_query:
        history_item = {
            "timestamp": time.strftime("%H:%M:%S"),
            "prompt": prompt_text,
            "sql": sql_query,
            "rows": len(results),
            "latency": latency_ms
        }
        if not st.session_state.query_history or st.session_state.query_history[0]["prompt"] != prompt_text:
            st.session_state.query_history.insert(0, history_item)
            if len(st.session_state.query_history) > 20:
                st.session_state.query_history.pop()


# ---------------------------------------------------------
# 6. HERO HEADER & CLEAN INPUT
# ---------------------------------------------------------
st.markdown("""
<div class="hero-container">
    <div class="hero-title">💬 Text to SQL Generator</div>
    <p class="hero-subtitle">
        Type what you want in plain English, and get the exact SQL query instantly.
    </p>
    <div class="hero-badge">
        <span class="pulse-dot"></span> 100% Free & Works for Everyone • No API Key Needed
    </div>
</div>
""", unsafe_allow_html=True)


def on_text_input_change():
    """Reactive callback fired immediately when user submits or changes text input."""
    new_input = st.session_state.user_query_input.strip()
    if new_input and new_input != st.session_state.last_executed_prompt:
        execute_query_pipeline(new_input)

col_input, col_btn = st.columns([5, 1])

with col_input:
    st.text_input(
        "Ask in English:",
        key="user_query_input",
        placeholder="Type any question, e.g. 'show me the duplicate items' or 'items cheaper than 100'...",
        on_change=on_text_input_change,
        label_visibility="collapsed"
    )

with col_btn:
    get_sql_btn = st.button("⚡ Get SQL", type="primary", use_container_width=True)


# Run query on initial load or button click
if get_sql_btn or not st.session_state.current_sql:
    active_prompt = st.session_state.user_query_input.strip()
    if active_prompt:
        with st.spinner("Translating..."):
            execute_query_pipeline(active_prompt)


# Optional AI Mode for open-ended questions
with st.expander("⚙️ Optional: Connect Free Gemini AI (For 100% open-ended questions)", expanded=False):
    st.markdown("""
    **Built-in Engine**: Works offline for everyone with zero setup.
    
    If you'd like **Google Gemini AI** to answer 100% of open-ended conversational prompts, paste a free key below (get one free at [aistudio.google.com](https://aistudio.google.com)):
    """)
    st.text_input(
        "Gemini API Key (Optional):",
        key="gemini_key_input",
        type="password",
        placeholder="Paste AIzaSy... (optional, leave blank to use free offline engine)",
        help="Optional. Leave blank to use the built-in offline engine."
    )

# ---------------------------------------------------------
# 7. GENERATED SQL QUERY (FULL WIDTH - NO SCROLLING NEEDED)
# ---------------------------------------------------------
st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

st.markdown('<div class="card-title">💻 Generated SQL Query:</div>', unsafe_allow_html=True)

if st.session_state.current_sql:
    # Full width with wrap_lines=True so entire query is visible without scrolling
    st.code(st.session_state.current_sql, language="sql", wrap_lines=True)
    
    explanation = explain_sql(st.session_state.current_sql)
    st.info(f"💡 **What it does:** {explanation}")
else:
    st.info("Type an English question above to see the SQL query.")
