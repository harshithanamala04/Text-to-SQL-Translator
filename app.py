# for running open terminal python app.py
# sqlite is a python inbuilt library
import sqlite3

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

mock_products = [('Laptop', 999.99), ('Earphones', 29.99), ('Phone', 699.99)]
cursor.executemany("INSERT INTO products (product_name, price) VALUES (?, ?);", mock_products)
connection.commit()


# 2. Our Rule-Based Translator Function
def translate_text_to_sql(user_input):
    # Convert input to lowercase to make parsing easier
    tokens = user_input.lower()
    
    # Base query structure
    query = "SELECT * FROM products"
    # Extract the number after "cheaper than"
    words = tokens.split()
    
    # Check for keywords to build the WHERE clause
    # Rule 1 --> Cheaper than (<)
    if "cheaper than" in tokens:
        # Find where "than" is, and take the next word (the price)
        try:
            than_index = words.index("than")
            # why +1 means after than we've space 
            price_value = words[than_index + 1].replace("$", "") # Remove dollar sign if present
            query += f" WHERE price < {price_value}"
        except (ValueError, IndexError):
            print("Could not parse the price value.")
    
    # Rule 2 --> Expensive than (>)
    elif "expensive than" in tokens or "more than" in tokens:
        try:
            than_index = words.index("than")
            price_value = words[than_index + 1].replace("$", "")
            query += f" WHERE price > {price_value}"
        except (ValueError, IndexError):
            print("Could not parse price.")
        
        
    # Rule 3 --> Exactly equal to (=)
    elif "exactly" in tokens or "costing" in tokens:
        try:
            keyword_index = words.index("exactly") if "exactly" in words else words.index("costing")
            price_value = words[keyword_index + 1].replace("$", "")
            query += f" WHERE price = {price_value}" # Single equals for SQL exact match!
        except (ValueError, IndexError):
            print("Could not parse exact price.")
            
    # Rule 4 --> Search by product name (text matching)
    elif "named" in tokens or "called" in tokens:
        try:
            keyword_index = words.index("named") if "named" in words else words.index("called")
            product_target = words[keyword_index + 1]
            
            # Capitalize it so it matches 'Laptop', 'Phone', etc. in our DB
            product_target = product_target.capitalize() 
            
            # Notice the single quotes added around the text value!
            query += f" WHERE product_name = '{product_target}'"
        except (ValueError, IndexError):
            print("Could not parse product name.")
            
    return query + ";"

# 3. Test the Translator
english_command = "find the product called phone"
generated_sql = translate_text_to_sql(english_command)

print(f"English Input: '{english_command}'")
print(f"Generated SQL:  {generated_sql}")

# 4. Run the generated SQL against our database
cursor.execute(generated_sql)
results = cursor.fetchall()
print(f"Database Results: {results}")