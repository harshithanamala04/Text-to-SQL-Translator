# Natural Language to SQL (NL2SQL) Translator Engine

A two-part Python-based translation engine that converts human English commands into structured SQL queries, executing them against an in-memory database with a Streamlit web UI.

---

## Architectural Evolution

### 1. The Rule-Based / Keyword Mapping Route (`app.py`)
We write Python code using string parsing to map words like `"show"`, `"find"`, or `"list"` to `SELECT`, and `"cheaper than"` to `<`. 
* **The Limitation:** Human language is messy. If someone types *"What's the cheapest item?"* or *"Give me everything under 50 bucks"*, our hardcoded string-matching rules break because they don't know what `"cheapest"` or `"bucks"` means.

### 2. The LLM (Large Language Model) Route (`ai_app.py` / `ui_app.py`)
Instead of hardcoding endless `if-elif` statements, we pass our database table structure to an AI and ask it to write the SQL query for us. This is where an LLM shines!

---

## 👥 The API Restaurant Analogy
To understand how our application securely routes requests to the AI model, we use this classic intermediary framework:
`Customer (Client Browser) <--> Waiter (Gemini API) <--> Kitchen (Google AI Server)`

---

## 🛠️ Installation & Environment Setup

### Required Package Installations
(a) Run these commands in your terminal to install the modern AI client engine and environment configurations:
##### pip install google-genai
(b) for storing secret API keys directly inside a programming project so they don't get pushed to GitHub, the industry standard is to use Environment Variables stored in a hidden file called a .env file
##### python-dotenv streamlit
(c) for running streamlit file use
##### streamlit run app.py