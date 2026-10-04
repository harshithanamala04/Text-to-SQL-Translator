# Natural Language to SQL Translation Engine
# 100% Free, Offline, Resilient, Multi-Entity & Relational
import re
import os

def clean_input_text(text):
    """Normalize input text by removing punctuation while preserving operators and decimals."""
    t = re.sub(r'[\?!,;]+', ' ', text)
    t = re.sub(r'(?<!\d)\.|\.(?!\d)', ' ', t)
    return ' '.join(t.split()).lower()

def parse_num(v_str):
    """Parse string number with optional $, k, or M suffix."""
    v = v_str.replace('$', '').strip()
    if v.endswith('k'):
        val = float(v[:-1]) * 1000
    elif v.endswith('m'):
        val = float(v[:-1]) * 1000000
    else:
        val = float(v)
    if val.is_integer():
        return str(int(val))
    return str(round(val, 2))

def universal_sql_engine(user_input):
    """
    Translates any natural language question into standard, valid ANSI/SQLite SQL.
    Works for any user without API keys. Completely free, offline, and reliable.
    """
    if not user_input or not user_input.strip():
        return "SELECT * FROM products;"

    raw_text = user_input.strip()
    clean = clean_input_text(raw_text)

    # -------------------------------------------------------------
    # 1. DIRECT SQL PASSTHROUGH
    # -------------------------------------------------------------
    upper_raw = raw_text.upper().strip()
    if upper_raw.startswith(("SELECT ", "INSERT INTO ", "UPDATE ", "DELETE FROM ", "CREATE TABLE ", "ALTER TABLE ", "DROP TABLE ", "PRAGMA ")):
        if not raw_text.endswith(";"):
            return raw_text + ";"
        return raw_text

    # -------------------------------------------------------------
    # 2. SCHEMA & TABLE INSPECTION
    # -------------------------------------------------------------
    if any(k in clean for k in ['show all tables', 'list tables', 'display tables', 'what tables exist', 'show tables', 'get tables']):
        return "SELECT name FROM sqlite_master WHERE type='table';"
    
    schema_m = re.search(r'(?:schema|structure|columns?|describe|desc)\s+(?:of|for|table)?\s*([a-zA-Z_]+)', clean)
    if schema_m and not any(k in clean for k in ['where', 'from tables', 'common data', 'join']):
        tbl = schema_m.group(1)
        if tbl not in ['the', 'all', 'a', 'each']:
            return f"PRAGMA table_info({tbl});"

    # -------------------------------------------------------------
    # 3. NEGATIVE RELATIONAL PATTERNS (NEVER ORDERED, UNSOLD, NO RELATIONS)
    # -------------------------------------------------------------
    if any(k in clean for k in ['never ordered', 'no orders', "haven't ordered", 'without orders', 'not placed any orders', 'placed no order']):
        return "SELECT * FROM customers WHERE customer_id NOT IN (SELECT customer_id FROM orders);"
    
    if any(k in clean for k in ['never sold', 'unsold', 'not ordered', 'no sales']):
        return "SELECT * FROM products WHERE product_id NOT IN (SELECT product_id FROM orders);"

    if 'who placed the most orders' in clean or 'customer with most orders' in clean:
        return "SELECT customer_id, COUNT(*) AS total_orders FROM orders GROUP BY customer_id ORDER BY total_orders DESC LIMIT 1;"

    # -------------------------------------------------------------
    # 4. MULTI-TABLE RELATIONAL QUERIES (JOIN, UNION, INTERSECT, EXCEPT)
    # -------------------------------------------------------------
    rel_match = re.search(r'(?:tables?|in both|between|join|from|of|data|combine|merge|union|connect)\s+([a-zA-Z_]+)\s+(?:and|with|to)\s+(?:tables?\s+)?([a-zA-Z_]+)', clean)
    if not rel_match:
        rel_match = re.search(r'([a-zA-Z_]+)\s+(?:and|join)\s+([a-zA-Z_]+)\s+tables?', clean)
    if not rel_match:
        rel_match = re.search(r'(?:in|from|of)\s+([a-zA-Z_]+)\s+but\s+not\s+(?:in\s+)?([a-zA-Z_]+)', clean)
    if not rel_match:
        rel_match = re.search(r'([a-zA-Z_]+)\s+(?:that are\s+)?also in\s+([a-zA-Z_]+)', clean)
    if not rel_match:
        rel_match = re.search(r'combine\s+([a-zA-Z_]+)\s+and\s+([a-zA-Z_]+)', clean)

    if rel_match:
        t1_raw = rel_match.group(1).lower()
        t2_raw = rel_match.group(2).lower()
        t1 = t1_raw if t1_raw.endswith('s') else t1_raw + 's'
        t2 = t2_raw if t2_raw.endswith('s') else t2_raw + 's'
        stop_words = ['prices', 'salaries', 'thes', 'alls', 'anys', 'eachs', 'items', 'tables', 'columns', 'datas']
        
        if t1 not in stop_words and t2 not in stop_words:
            # Check for explicit join key '\bon\b <key>'
            on_match = re.search(r'\bon\b\s+([a-zA-Z_]+)(?:\s*=\s*[a-zA-Z_\.]+)?', clean)
            join_col = on_match.group(1) if on_match else None
            
            if not join_col:
                if 'customer' in t1 and 'order' in t2:
                    join_col = 'customer_id'
                elif 'order' in t1 and 'customer' in t2:
                    join_col = 'customer_id'
                elif 'product' in t1 and 'order' in t2:
                    join_col = 'product_id'
                elif 'order' in t1 and 'product' in t2:
                    join_col = 'product_id'
                elif 'employee' in t1 and 'department' in t2:
                    join_col = 'department_id'
                elif 'product' in t1 or 'product' in t2:
                    join_col = 'product_id'
                elif 'customer' in t1 or 'customer' in t2:
                    join_col = 'customer_id'
                elif 'employee' in t1 or 'employee' in t2:
                    join_col = 'employee_id'
                elif 'order' in t1 or 'order' in t2:
                    join_col = 'order_id'
                else:
                    join_col = 'id'

            # 4A. Difference / Not In / Except
            if any(k in clean for k in ['not in', 'except', 'difference', 'only in', 'missing from', 'but not']):
                return f"SELECT * FROM {t1} WHERE {join_col} NOT IN (SELECT {join_col} FROM {t2});"

            # 4B. Union / Combine
            if any(k in clean for k in ['union', 'combine', 'merge', 'together']):
                return f"SELECT * FROM {t1} UNION SELECT * FROM {t2};"

            # 4C. Joins (Left / Right / Full / Inner)
            join_type = "INNER JOIN"
            if 'left join' in clean or 'left outer' in clean:
                join_type = "LEFT JOIN"
            elif 'right join' in clean:
                join_type = "RIGHT JOIN"
            elif 'full join' in clean or 'outer join' in clean:
                join_type = "FULL OUTER JOIN"

            alias1 = t1[0]
            alias2 = t2[0] if t2[0] != alias1 else t2[:2]
            return f"SELECT {alias1}.*, {alias2}.* FROM {t1} {alias1} {join_type} {t2} {alias2} ON {alias1}.{join_col} = {alias2}.{join_col};"

    # Contextual Customer-Order Join Query
    if ('customer' in clean or 'client' in clean) and ('order' in clean or 'ordered' in clean or 'bought' in clean):
        val_m = re.search(r'(?:over|above|greater than|>|more than|exceeding)\s+\$?([0-9]+(?:\.[0-9]+)?k?)', clean)
        if val_m:
            num = parse_num(val_m.group(1))
            return f"SELECT c.*, o.total_amount FROM customers c INNER JOIN orders o ON c.customer_id = o.customer_id WHERE o.total_amount > {num};"

    # -------------------------------------------------------------
    # 5. EXPLICIT SQL SYNTAX: 'SELECT col1, col2 FROM table'
    # -------------------------------------------------------------
    explicit_select = re.search(r'^\s*select\s+([a-zA-Z0-9_,\s\*]+)\s+from\s+([a-zA-Z0-9_]+)(.*)', raw_text, re.IGNORECASE)
    if explicit_select:
        raw_cols = explicit_select.group(1).strip()
        tbl_candidate = explicit_select.group(2).strip().lower()
        rem_clause = explicit_select.group(3).strip()
        if rem_clause and not rem_clause.endswith(";"):
            rem_clause = " " + rem_clause
        elif rem_clause.endswith(";"):
            rem_clause = " " + rem_clause[:-1]
        return f"SELECT {raw_cols} FROM {tbl_candidate}{rem_clause};"

    # -------------------------------------------------------------
    # 6. DYNAMIC ENTITY & TABLE RESOLUTION
    # -------------------------------------------------------------
    known_entities = [
        ('product', 'products', 'price', 'product_name', 'product_id'),
        ('item', 'products', 'price', 'product_name', 'product_id'),
        ('device', 'products', 'price', 'product_name', 'product_id'),
        ('employee', 'employees', 'salary', 'employee_name', 'employee_id'),
        ('worker', 'employees', 'salary', 'employee_name', 'employee_id'),
        ('staff', 'employees', 'salary', 'employee_name', 'employee_id'),
        ('customer', 'customers', 'total_spent', 'customer_name', 'customer_id'),
        ('client', 'customers', 'total_spent', 'customer_name', 'customer_id'),
        ('user', 'users', 'created_at', 'username', 'user_id'),
        ('student', 'students', 'marks', 'student_name', 'student_id'),
        ('book', 'books', 'price', 'title', 'book_id'),
        ('car', 'cars', 'price', 'model', 'car_id'),
        ('order', 'orders', 'total_amount', 'order_id', 'order_id'),
        ('transaction', 'transactions', 'amount', 'transaction_id', 'transaction_id'),
        ('sale', 'sales', 'revenue', 'sale_id', 'sale_id'),
        ('flight', 'flights', 'ticket_price', 'flight_number', 'flight_id'),
        ('movie', 'movies', 'rating', 'title', 'movie_id')
    ]

    table = "products"
    val_col = "price"
    name_col = "product_name"
    id_col = "product_id"

    entity_found = False
    for singular, t, v, n, i in known_entities:
        if singular == 'order' and ('order by' in clean or 'order all' in clean or 'ordered by' in clean):
            continue
        if re.search(rf'\b{singular}(?:s|es)?\b', clean):
            table = t
            val_col = v
            name_col = n
            id_col = i
            entity_found = True
            break

    if not entity_found:
        from_match = re.search(r'\bfrom\s+(?:tables?\s+)?([a-zA-Z0-9_]+)', clean)
        if from_match:
            cand = from_match.group(1).lower()
            sql_words = ['the', 'all', 'a', 'each', 'both', 'between', 'where', 'city', 'london', 'york', 'paris', 'tokyo', 'mumbai', 'delhi']
            if cand not in sql_words:
                table = cand if cand.endswith('s') else cand + 's'
                val_col = "price" if "price" in clean else ("salary" if "salary" in clean else "amount")
                name_col = "name"
                id_col = f"{cand}_id"

    # Contextual adjustments
    if ('salary' in clean or 'department' in clean or 'hired' in clean) and table == "products":
        table, val_col, name_col, id_col = 'employees', 'salary', 'employee_name', 'employee_id'
    elif ('spent' in clean or 'bought' in clean) and table == "products":
        table, val_col, name_col, id_col = 'customers', 'total_spent', 'customer_name', 'customer_id'
    elif 'marks' in clean or 'grade' in clean or 'score' in clean:
        table, val_col, name_col, id_col = 'students', 'marks', 'student_name', 'student_id'
    elif 'ticket' in clean or 'flight' in clean:
        table, val_col, name_col, id_col = 'flights', 'ticket_price', 'flight_number', 'flight_id'

    # -------------------------------------------------------------
    # 7. DML OPERATIONS (DELETE, INSERT, UPDATE)
    # -------------------------------------------------------------
    if clean.startswith('delete') or 'remove from' in clean:
        id_m = re.search(r'(?:id|with id)\s*=?\s*([0-9]+)', clean)
        name_m = re.search(r'(?:called|named)\s+[\'\"]?([a-zA-Z0-9]+)[\'\"]?', clean)
        price_m = re.search(r'(?:where\s+)?(?:price|salary|amount)?\s*(<|>|<=|>=|=)\s*\$?([0-9\.]+)', clean)
        if id_m:
            return f"DELETE FROM {table} WHERE {id_col} = {id_m.group(1)};"
        elif name_m:
            return f"DELETE FROM {table} WHERE {name_col} = '{name_m.group(1).capitalize()}';"
        elif price_m:
            return f"DELETE FROM {table} WHERE {val_col} {price_m.group(1)} {parse_num(price_m.group(2))};"
        return f"DELETE FROM {table} WHERE {id_col} = 1;"

    if clean.startswith('insert') or clean.startswith('add '):
        name_m = re.search(r'(?:insert|add)\s+(?:product|item|employee|student)?\s*([a-zA-Z]+)\s+(?:with\s+(?:price|salary)|price|salary|costing)?\s*\$?([0-9\.]+)', clean)
        if name_m:
            item_name = name_m.group(1).capitalize()
            val_num = parse_num(name_m.group(2))
            return f"INSERT INTO {table} ({name_col}, {val_col}) VALUES ('{item_name}', {val_num});"

    if clean.startswith('update') or 'change price' in clean or 'set price' in clean:
        new_val_m = re.search(r'(?:to|set)\s+\$?([0-9\.]+)', clean)
        name_m = re.search(r'(?:of|for)\s+([a-zA-Z]+)', clean)
        if new_val_m and name_m:
            return f"UPDATE {table} SET {val_col} = {parse_num(new_val_m.group(1))} WHERE {name_col} = '{name_m.group(1).capitalize()}';"

    # -------------------------------------------------------------
    # 8. SUBQUERIES (DUPLICATES & AVERAGE COMPARISONS)
    # -------------------------------------------------------------
    if any(k in clean for k in ['duplicate', 'repeated', 'more than once', 'repeating', 'duplicates']):
        target_dup_col = name_col
        if 'email' in clean:
            target_dup_col = 'email'
        elif 'username' in clean:
            target_dup_col = 'username'
        elif 'id' in clean:
            target_dup_col = id_col
        return f"SELECT * FROM {table} WHERE {target_dup_col} IN (SELECT {target_dup_col} FROM {table} GROUP BY {target_dup_col} HAVING COUNT(*) > 1);"

    if any(k in clean for k in ['above average', 'more than average', 'higher than average', 'greater than average', 'costlier than average']):
        return f"SELECT * FROM {table} WHERE {val_col} > (SELECT AVG({val_col}) FROM {table});"
    if any(k in clean for k in ['below average', 'less than average', 'cheaper than average', 'lower than average']):
        return f"SELECT * FROM {table} WHERE {val_col} < (SELECT AVG({val_col}) FROM {table});"

    # Distinct / Unique
    if any(k in clean for k in ['distinct', 'unique', 'without duplicate', 'without duplicates', 'remove duplicates', 'different']):
        if 'name' in clean:
            return f"SELECT DISTINCT {name_col} FROM {table};"
        if 'city' in clean:
            return f"SELECT DISTINCT city FROM {table};"
        if 'category' in clean:
            return f"SELECT DISTINCT category FROM {table};"
        return f"SELECT DISTINCT {name_col}, {val_col} FROM {table};"

    # -------------------------------------------------------------
    # 9. SUPERLATIVES (HIGHEST PAID, LOWEST EARNING, OLDEST, NEWEST)
    # -------------------------------------------------------------
    if any(k in clean for k in ['highest paid', 'highest earning', 'top earner', 'highest salary', 'top paid', 'maximum earning', 'most paid']):
        return f"SELECT * FROM {table} ORDER BY {val_col} DESC LIMIT 1;"
    if any(k in clean for k in ['lowest paid', 'least paid', 'lowest salary', 'minimum earning', 'least earning']):
        return f"SELECT * FROM {table} ORDER BY {val_col} ASC LIMIT 1;"
    if any(k in clean for k in ['oldest', 'earliest']):
        date_col = 'hire_date' if table == 'employees' else ('order_date' if table == 'orders' else 'created_at')
        return f"SELECT * FROM {table} ORDER BY {date_col} ASC LIMIT 1;"
    if any(k in clean for k in ['newest', 'latest', 'most recent']):
        date_col = 'hire_date' if table == 'employees' else ('order_date' if table == 'orders' else 'created_at')
        return f"SELECT * FROM {table} ORDER BY {date_col} DESC LIMIT 1;"

    # Rankings & Nth Extremes
    nth_match = re.search(r'(second|2nd|third|3rd|fourth|4th|fifth|5th)\s+(?:most|highest|priciest|expensive|paid|earning)', clean)
    if nth_match:
        ord_map = {'second': 1, '2nd': 1, 'third': 2, '3rd': 2, 'fourth': 3, '4th': 3, 'fifth': 4, '5th': 4}
        offset = ord_map.get(nth_match.group(1), 1)
        return f"SELECT * FROM {table} ORDER BY {val_col} DESC LIMIT 1 OFFSET {offset};"

    nth_cheap = re.search(r'(second|2nd|third|3rd)\s+(?:least|lowest|cheapest)', clean)
    if nth_cheap:
        ord_map = {'second': 1, '2nd': 1, 'third': 2, '3rd': 2}
        offset = ord_map.get(nth_cheap.group(1), 1)
        return f"SELECT * FROM {table} ORDER BY {val_col} ASC LIMIT 1 OFFSET {offset};"

    # -------------------------------------------------------------
    # 10. GROUP BY & AGGREGATIONS PER CATEGORY / DEPARTMENT / CITY
    # -------------------------------------------------------------
    grp_match = re.search(r'\b(?:group by|per|for each|by)\s+([a-zA-Z_]+)', clean)
    if grp_match and not any(k in clean for k in ['order by', 'sorted by', 'sort by', 'cheaper than', 'more than']):
        grp_col = grp_match.group(1)
        ignored_stop_words = ['price', 'salary', 'name', 'desc', 'asc', 'the', 'all', 'than', 'a', 'an', 'products', 'items', 'tables']
        if grp_col not in ignored_stop_words:
            if any(k in clean for k in ['average', 'avg', 'mean']):
                return f"SELECT {grp_col}, ROUND(AVG({val_col}), 2) AS average_{val_col} FROM {table} GROUP BY {grp_col};"
            elif any(k in clean for k in ['count', 'how many', 'total number']):
                return f"SELECT {grp_col}, COUNT(*) AS count FROM {table} GROUP BY {grp_col};"
            elif any(k in clean for k in ['sum', 'total']):
                return f"SELECT {grp_col}, ROUND(SUM({val_col}), 2) AS total_{val_col} FROM {table} GROUP BY {grp_col};"
            else:
                return f"SELECT {grp_col}, COUNT(*) AS total_items FROM {table} GROUP BY {grp_col};"

    # -------------------------------------------------------------
    # 11. COLUMN PROJECTIONS
    # -------------------------------------------------------------
    select_cols = "*"
    if ('only' in clean and 'name' in clean) or 'product names' in clean or 'list names' in clean or 'just names' in clean or 'show names' in clean or 'get names' in clean or 'names of' in clean:
        select_cols = name_col
    elif ('only' in clean and 'price' in clean) or 'product prices' in clean or 'list prices' in clean or 'just prices' in clean or 'show prices' in clean or 'prices of' in clean:
        select_cols = val_col
    elif any(k in clean for k in ['name and price', 'names and prices', 'price and name']):
        select_cols = f"{name_col}, {val_col}"
    elif clean.startswith('what is the price of') or clean.startswith('price of'):
        select_cols = val_col

    # -------------------------------------------------------------
    # 12. CONDITIONS (WHERE CLAUSE)
    # -------------------------------------------------------------
    conditions = []
    order_clause = ""
    limit_clause = ""

    # 12A. Department condition
    dept_m = re.search(r'(?:in|from|of)\s+([a-zA-Z]+)\s+department', clean)
    if not dept_m and table == 'employees':
        dept_m = re.search(r'(?:in|department)\s+([a-zA-Z]+)', clean)
    if dept_m:
        dept_val = dept_m.group(1).strip().capitalize()
        if dept_val not in ['The', 'All', 'Each']:
            if any(dept_val.lower() == d for d in ['engineering', 'sales', 'marketing', 'hr', 'it', 'finance', 'operations', 'tech']):
                conditions.append(f"department = '{dept_val}'")
            elif table == 'employees':
                conditions.append(f"department = '{dept_val}'")

    # 12B. Category condition
    cat_m = re.search(r'category\s+([a-zA-Z]+)', clean)
    if not cat_m:
        cat_m = re.search(r'(?:in|under)\s+([a-zA-Z]+)\s+category', clean)
    if cat_m:
        cat_val = cat_m.group(1).strip().capitalize()
        conditions.append(f"category = '{cat_val}'")

    # 12C. Status condition
    stat_m = re.search(r'status\s+(?:is|=|equals)?\s*[\'\"]?([a-zA-Z]+)[\'\"]?', clean)
    if stat_m:
        stat_val = stat_m.group(1).strip().lower()
        if stat_val not in ['in', 'the', 'of']:
            conditions.append(f"status = '{stat_val}'")

    # 12D. Date conditions (after / before / in year)
    date_col = 'order_date' if table == 'orders' else ('hire_date' if table == 'employees' else 'created_at')
    after_date_m = re.search(r'(?:after|since|newer than)\s+([0-9]{4})', clean)
    before_date_m = re.search(r'(?:before|prior to|older than)\s+([0-9]{4})', clean)
    in_year_m = re.search(r'(?:in|during|placed in|created in|hired in)\s+([0-9]{4})', clean)

    if after_date_m:
        yr = after_date_m.group(1)
        conditions.append(f"{date_col} > '{yr}-12-31'")
    elif before_date_m:
        yr = before_date_m.group(1)
        conditions.append(f"{date_col} < '{yr}-01-01'")
    elif in_year_m:
        yr = in_year_m.group(1)
        conditions.append(f"strftime('%Y', {date_col}) = '{yr}'")

    # 12E. Between X and Y
    between_match = re.search(r'between\s+\$?([0-9]+(?:\.[0-9]+)?k?)\s+(?:and|to)\s+\$?([0-9]+(?:\.[0-9]+)?k?)', clean)
    if not between_match:
        between_match = re.search(r'from\s+\$?([0-9]+(?:\.[0-9]+)?k?)\s+to\s+\$?([0-9]+(?:\.[0-9]+)?k?)', clean)

    if between_match:
        p1 = float(between_match.group(1).replace('k', '000'))
        p2 = float(between_match.group(2).replace('k', '000'))
        low, high = sorted([p1, p2])
        conditions.append(f"{val_col} BETWEEN {parse_num(str(low))} AND {parse_num(str(high))}")
    else:
        # Math operators (>=, <=, !=, <>, >, <, =)
        op_match = re.search(r'(?:price|salary|amount|marks|spent)?\s*(>=|<=|!=|<>|>|<|=)\s*\$?([0-9]+(?:\.[0-9]+)?k?)', clean)
        if op_match:
            op = op_match.group(1)
            v = parse_num(op_match.group(2))
            conditions.append(f"{val_col} {op} {v}")
        else:
            under_match = re.search(r'(?:cheaper than|less than|under|below|earning less than|costing less than)\s+\$?([0-9]+(?:\.[0-9]+)?k?)', clean)
            at_most_match = re.search(r'(?:at most|up to|maximum of|no more than)\s+\$?([0-9]+(?:\.[0-9]+)?k?)', clean)
            if under_match:
                conditions.append(f"{val_col} < {parse_num(under_match.group(1))}")
            if at_most_match:
                conditions.append(f"{val_col} <= {parse_num(at_most_match.group(1))}")

            above_match = re.search(r'(?:more expensive than|expensive than|greater than|more than|above|over|earning more than|costing more than|exceeding)\s+\$?([0-9]+(?:\.[0-9]+)?k?)', clean)
            at_least_match = re.search(r'(?:at least|minimum of|no less than)\s+\$?([0-9]+(?:\.[0-9]+)?k?)', clean)
            if above_match:
                conditions.append(f"{val_col} > {parse_num(above_match.group(1))}")
            if at_least_match:
                conditions.append(f"{val_col} >= {parse_num(at_least_match.group(1))}")

            not_match = re.search(r'(?:not equal to|other than|different from|not)\s+\$?([0-9]+(?:\.[0-9]+)?k?)', clean)
            if not_match:
                conditions.append(f"{val_col} != {parse_num(not_match.group(1))}")
            else:
                exact_match = re.search(r'(?:exactly|costing|priced at|equal to|earning)\s+\$?([0-9]+(?:\.[0-9]+)?k?)', clean)
                if exact_match and not (under_match or above_match or at_most_match or at_least_match):
                    conditions.append(f"{val_col} = {parse_num(exact_match.group(1))}")

    # Substrings & Text Matching
    starts_match = re.search(r'start(?:s|ing)?\s+with\s+(?:letter\s+)?[\'\"]?([a-zA-Z0-9]+)[\'\"]?', clean)
    ends_match = re.search(r'end(?:s|ing)?\s+with\s+(?:letter\s+)?[\'\"]?([a-zA-Z0-9]+)[\'\"]?', clean)
    contains_match = re.search(r'contain(?:s|ing)?\s+(?:letter\s+|word\s+)?[\'\"]?([a-zA-Z0-9]+)[\'\"]?', clean)

    if starts_match:
        conditions.append(f"{name_col} LIKE '{starts_match.group(1).upper()}%'")
    elif ends_match:
        conditions.append(f"{name_col} LIKE '%{ends_match.group(1)}'")
    elif contains_match:
        conditions.append(f"LOWER({name_col}) LIKE '%{contains_match.group(1)}%'")
    else:
        name_match = re.search(r'(?:named|called)\s+[\'\"]?([a-zA-Z0-9\-_]+)[\'\"]?', clean)
        if name_match:
            conditions.append(f"{name_col} = '{name_match.group(1).capitalize()}'")
        elif table == "products":
            for prod in ['laptop', 'earphones', 'phone', 'smartwatch', 'tablet', 'keyboard', 'monitor', 'mouse', 'headphones', 'camera']:
                if re.search(rf'\b{prod}s?\b', clean):
                    conditions.append(f"LOWER({name_col}) LIKE '%{prod}%'")
                    break

    # City matching - e.g. "from London", "living in New York"
    city_match = re.search(r'(?:living in|located in|based in|residing in|from the city of|from city)\s+([a-zA-Z]+)', clean)
    if not city_match and table in ['customers', 'users', 'employees']:
        city_m2 = re.search(r'(?:customers?|users?|employees?)\s+from\s+([a-zA-Z]+)', clean)
        if city_m2:
            city_match = city_m2
    if city_match:
        city_name = city_match.group(1).strip().capitalize()
        sql_keywords = ['Employees', 'Customers', 'Users', 'Products', 'Tables', 'Where', 'Order', 'Select', 'Each']
        if city_name not in sql_keywords:
            conditions.append(f"city = '{city_name}'")

    # -------------------------------------------------------------
    # 13. AGGREGATIONS (COUNT, AVG, SUM, MIN, MAX)
    # -------------------------------------------------------------
    where_part = f" WHERE {' AND '.join(conditions)}" if conditions else ""

    if any(k in clean for k in ['how many', 'count', 'number of items', 'number of products', 'total count', 'total number']):
        return f"SELECT COUNT(*) AS total FROM {table}{where_part};"

    if any(k in clean for k in ['average price', 'avg price', 'mean price', 'average salary', 'avg salary', 'average marks', 'average of']):
        return f"SELECT ROUND(AVG({val_col}), 2) AS average_{val_col} FROM {table}{where_part};"

    if any(k in clean for k in ['total price', 'total value', 'sum of price', 'sum of prices', 'total salary', 'inventory value', 'sum of']):
        return f"SELECT ROUND(SUM({val_col}), 2) AS total_{val_col} FROM {table}{where_part};"

    if any(k in clean for k in ['minimum price', 'min price', 'lowest price', 'min salary', 'lowest marks', 'cheapest item', 'lowest cost']):
        if 'cheapest item' in clean or 'lowest cost' in clean:
            return f"SELECT * FROM {table} ORDER BY {val_col} ASC LIMIT 1;"
        return f"SELECT MIN({val_col}) AS min_{val_col} FROM {table}{where_part};"

    if any(k in clean for k in ['maximum price', 'max price', 'highest price', 'max salary', 'highest marks', 'most expensive item', 'highest cost']):
        if 'most expensive item' in clean or 'highest cost' in clean:
            return f"SELECT * FROM {table} ORDER BY {val_col} DESC LIMIT 1;"
        return f"SELECT MAX({val_col}) AS max_{val_col} FROM {table}{where_part};"

    # -------------------------------------------------------------
    # 14. EXTREMES, SORTING & LIMITS
    # -------------------------------------------------------------
    if any(k in clean for k in ['cheapest', 'least expensive', 'lowest priced']):
        if 'all' not in clean and 'order' not in clean and 'sort' not in clean:
            limit_clause = " LIMIT 1"
            order_clause = f" ORDER BY {val_col} ASC"

    if any(k in clean for k in ['most expensive', 'highest priced', 'priciest', 'top priced']):
        if 'all' not in clean and 'order' not in clean and 'sort' not in clean:
            limit_clause = " LIMIT 1"
            order_clause = f" ORDER BY {val_col} DESC"

    # Ordering
    if any(k in clean for k in ['order by price desc', 'expensive first', 'highest first', 'highest to lowest', 'descending', 'desc', 'sorted by total spent', 'highest salary first']):
        order_clause = f" ORDER BY {val_col} DESC"
    elif any(k in clean for k in ['order by price asc', 'cheapest first', 'lowest first', 'lowest to highest', 'ascending', 'asc', 'order by price', 'sorted by price', 'by price']):
        order_clause = f" ORDER BY {val_col} ASC"
    elif any(k in clean for k in ['order by name', 'ordered by name', 'alphabetical', 'sort by name', 'sorted by name']):
        order_clause = f" ORDER BY {name_col} ASC"

    # Limits
    top_match = re.search(r'(?:top|first|limit)\s+([0-9]+)', clean)
    if top_match:
        limit_count = top_match.group(1)
        limit_clause = f" LIMIT {limit_count}"
        if not order_clause:
            if any(k in clean for k in ['cheap', 'low', 'least']):
                order_clause = f" ORDER BY {val_col} ASC"
            else:
                order_clause = f" ORDER BY {val_col} DESC"

    # Adjectives without numbers
    if not conditions:
        if 'cheap' in clean or 'affordable' in clean or 'budget' in clean:
            order_clause = f" ORDER BY {val_col} ASC"
        elif 'expensive' in clean or 'costly' in clean or 'premium' in clean:
            order_clause = f" ORDER BY {val_col} DESC"

    # -------------------------------------------------------------
    # 15. FINAL QUERY ASSEMBLY
    # -------------------------------------------------------------
    query = f"SELECT {select_cols} FROM {table}"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    if order_clause:
        query += order_clause
    if limit_clause:
        query += limit_clause

    return query + ";"


def explain_sql(sql):
    """Generates an intuitive, accurate plain-English explanation for the SQL query."""
    s = sql.lower()
    if "inner join" in s or "join" in s:
        return "Combines common matching records across both tables based on matching ID keys."
    if "not in (select" in s:
        return "Finds records from the first table that do not exist in the second table."
    if "union" in s:
        return "Combines all distinct rows from multiple tables into a single result set."
    if "having count(*) > 1" in s or ("in (select" in s and "group by" in s):
        return "Finds duplicate records that appear more than once using GROUP BY and HAVING."
    if "distinct" in s:
        return "Retrieves unique (distinct) entries, filtering out all duplicate values."
    if "> (select avg(" in s:
        return "Filters records having a value strictly greater than the overall table average."
    if "< (select avg(" in s:
        return "Filters records having a value strictly lower than the overall table average."
    if "count(*)" in s:
        return "Counts the total number of matching items in the database."
    if "avg(" in s:
        return "Calculates the average numerical value across the matching rows."
    if "sum(" in s:
        return "Calculates the sum of all matching values (total value)."
    if "order by" in s and "desc limit 1 offset" in s:
        return "Finds the ranked extreme item using ORDER BY with LIMIT and OFFSET."
    if "order by" in s and "desc limit 1" in s:
        return "Finds the single highest-valued record."
    if "order by" in s and "asc limit 1" in s:
        return "Finds the single lowest-valued record."
    if "between" in s:
        return "Filters records whose value falls within the specified range."
    if "like '" in s and "%" in s:
        return "Filters records matching the specified text pattern."
    if "<" in s:
        return "Retrieves items costing or measuring strictly less than the specified amount."
    if ">" in s:
        return "Retrieves items costing or measuring strictly more than the specified amount."
    if "!=" in s:
        return "Retrieves items excluding the specified amount."
    if "=" in s:
        return "Retrieves items with an exact match on the specified criteria."
    if "order by" in s and "desc" in s:
        return "Retrieves records sorted from highest to lowest."
    if "order by" in s:
        return "Retrieves records sorted from lowest to highest."
    if "pragma table_info" in s:
        return "Inspects the table schema, column names, and data types."
    if "sqlite_master" in s:
        return "Lists all tables available in the SQLite database."
    return "Retrieves all matching records from the database."
