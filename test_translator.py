# Automated Test Suite for Natural Language to SQL Translation Engine
import unittest
from engine import universal_sql_engine, explain_sql

class TestSQLTranslator(unittest.TestCase):

    def test_multi_table_relational(self):
        q = "want common data from tables products and customers"
        sql = universal_sql_engine(q)
        self.assertIn("INNER JOIN", sql)
        self.assertIn("products", sql)
        self.assertIn("customers", sql)
        self.assertIn("ON p.product_id = c.product_id", sql)

        q2 = "show common data between customers and orders"
        sql2 = universal_sql_engine(q2)
        self.assertIn("INNER JOIN", sql2)
        self.assertIn("customers", sql2)
        self.assertIn("orders", sql2)

        q3 = "products in products but not in orders"
        sql3 = universal_sql_engine(q3)
        self.assertIn("NOT IN (SELECT product_id FROM orders)", sql3)

        q4 = "combine products and archived_products"
        sql4 = universal_sql_engine(q4)
        self.assertEqual(sql4, "SELECT * FROM products UNION SELECT * FROM archived_products;")

    def test_aggregations_and_grouping(self):
        q1 = "how many orders are there"
        self.assertEqual(universal_sql_engine(q1), "SELECT COUNT(*) AS total FROM orders;")

        q2 = "average salary of employees by department"
        self.assertEqual(universal_sql_engine(q2), "SELECT department, ROUND(AVG(salary), 2) AS average_salary FROM employees GROUP BY department;")

    def test_filtering_and_bounds(self):
        q1 = "find products with price between 20 and 100"
        self.assertEqual(universal_sql_engine(q1), "SELECT * FROM products WHERE price BETWEEN 20 AND 100;")

        q2 = "get all records from employees where salary > 50000"
        self.assertEqual(universal_sql_engine(q2), "SELECT * FROM employees WHERE salary > 50000;")

        q3 = "products cheaper than 50 dollars"
        self.assertEqual(universal_sql_engine(q3), "SELECT * FROM products WHERE price < 50;")

    def test_subqueries_and_duplicates(self):
        q1 = "find duplicate email in users table"
        self.assertEqual(universal_sql_engine(q1), "SELECT * FROM users WHERE email IN (SELECT email FROM users GROUP BY email HAVING COUNT(*) > 1);")

        q2 = "employees earning more than average salary"
        self.assertEqual(universal_sql_engine(q2), "SELECT * FROM employees WHERE salary > (SELECT AVG(salary) FROM employees);")

    def test_advanced_nlp_patterns(self):
        q1 = "who is the highest paid employee"
        self.assertEqual(universal_sql_engine(q1), "SELECT * FROM employees ORDER BY salary DESC LIMIT 1;")

        q2 = "show all employees in engineering department"
        self.assertEqual(universal_sql_engine(q2), "SELECT * FROM employees WHERE department = 'Engineering';")

        q3 = "list products with price less than 50 and category electronics"
        self.assertEqual(universal_sql_engine(q3), "SELECT * FROM products WHERE category = 'Electronics' AND price < 50;")

        q4 = "orders created after 2023"
        self.assertEqual(universal_sql_engine(q4), "SELECT * FROM orders WHERE order_date > '2023-12-31';")

        q5 = "customers who have never ordered"
        self.assertEqual(universal_sql_engine(q5), "SELECT * FROM customers WHERE customer_id NOT IN (SELECT customer_id FROM orders);")

        q6 = "what is the average price of laptops"
        self.assertEqual(universal_sql_engine(q6), "SELECT ROUND(AVG(price), 2) AS average_price FROM products WHERE LOWER(product_name) LIKE '%laptop%';")

if __name__ == "__main__":
    unittest.main()
