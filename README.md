# 💬 Text to SQL Translator

An intuitive, real-time web application that converts plain English questions into clean, optimized SQL queries.

🌐 **Live Application:** [https://text-to-sql-translator-b392abrajd5xc3j2hdfg3k.streamlit.app/](https://text-to-sql-translator-b392abrajd5xc3j2hdfg3k.streamlit.app/)

---

## ⚡ Features

- **100% Free & Offline by Default:** Generates accurate SQL queries with sub-millisecond latency without requiring any API keys.
- **Relational & Multi-Table Joins:** Handles `INNER JOIN`, `LEFT JOIN`, `UNION`, and `EXCEPT` operations across multiple tables.
- **Advanced Query Parsing:** Supports aggregations (`COUNT`, `AVG`, `SUM`, `MIN`, `MAX`), date conditions, superlatives (e.g., *highest paid employee*), and complex filtering.
- **Plain-English Explanations:** Explains what each generated SQL query accomplishes in simple terms.
- **Optional Gemini AI Mode:** Connect a free Google Gemini API key anytime for 100% open-ended conversational questions.

---

## 🚀 Quickstart (Run Locally)

### 1. Clone the repository
```bash
git clone https://github.com/harshithanamala04/Text-to-SQL-Translator.git
cd Text-to-SQL-Translator
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the web app
```bash
streamlit run ui_app.py
```
Open your browser at `http://localhost:8501`.

---

## 📂 Project Structure

- `ui_app.py` — Streamlit interactive web application
- `engine.py` — High-precision natural language to SQL translation engine
- `app.py` — CLI runner and entrypoint
- `test_translator.py` — Automated unit test suite
- `requirements.txt` — Python dependencies

---

## 📄 License
MIT License
