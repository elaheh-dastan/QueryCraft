"""
Tests for SQLAgent._clean_sql_query static method
"""

from django.test import TestCase

from querycraft.services import SQLAgent


class TestCleanSQLQuery(TestCase):
    """Test cases for _clean_sql_query static method"""

    def test_simple_select_query(self) -> None:
        """Test cleaning a simple SELECT query without any wrapping"""
        sql = "SELECT * FROM querycraft_customer"
        result = SQLAgent._clean_sql_query(sql)
        self.assertEqual(result, "SELECT * FROM querycraft_customer")

    def test_query_with_trailing_semicolon(self) -> None:
        """Test that trailing semicolons are removed"""
        sql = "SELECT * FROM querycraft_product;"
        result = SQLAgent._clean_sql_query(sql)
        self.assertEqual(result, "SELECT * FROM querycraft_product")

    def test_query_with_markdown_code_block(self) -> None:
        """Test cleaning SQL wrapped in markdown code blocks"""
        sql = "```sql\nSELECT * FROM querycraft_order\n```"
        result = SQLAgent._clean_sql_query(sql)
        self.assertEqual(result, "SELECT * FROM querycraft_order")

    def test_query_with_markdown_no_language_identifier(self) -> None:
        """Test cleaning SQL in markdown without language identifier"""
        sql = "```\nSELECT id, name FROM querycraft_customer\n```"
        result = SQLAgent._clean_sql_query(sql)
        self.assertEqual(result, "SELECT id, name FROM querycraft_customer")

    def test_query_with_uppercase_sql_identifier(self) -> None:
        """Test markdown with uppercase SQL identifier"""
        sql = "```SQL\nSELECT * FROM querycraft_product\n```"
        result = SQLAgent._clean_sql_query(sql)
        self.assertEqual(result, "SELECT * FROM querycraft_product")

    def test_query_with_extra_text_before(self) -> None:
        """Test extracting SQL when there's explanatory text before it"""
        sql = "Here is the query you requested:\nSELECT * FROM querycraft_customer WHERE id = 1"
        result = SQLAgent._clean_sql_query(sql)
        self.assertEqual(result, "SELECT * FROM querycraft_customer WHERE id = 1")

    def test_query_with_extra_text_after(self) -> None:
        """Test that text after semicolon is ignored"""
        sql = "SELECT * FROM querycraft_order;\nThis query returns all orders."
        result = SQLAgent._clean_sql_query(sql)
        self.assertEqual(result, "SELECT * FROM querycraft_order")

    def test_multiline_query(self) -> None:
        """Test cleaning a multiline SQL query"""
        sql = """SELECT
            c.name,
            COUNT(o.id) as order_count
        FROM querycraft_customer c
        LEFT JOIN querycraft_order o ON c.id = o.customer_id
        GROUP BY c.name"""
        result = SQLAgent._clean_sql_query(sql)
        expected = "SELECT c.name, COUNT(o.id) as order_count FROM querycraft_customer c LEFT JOIN querycraft_order o ON c.id = o.customer_id GROUP BY c.name"
        self.assertEqual(result, expected)

    def test_multiline_query_in_markdown(self) -> None:
        """Test cleaning multiline SQL in markdown"""
        sql = """```sql
        SELECT
            p.name,
            p.price
        FROM querycraft_product p
        WHERE p.category = 'electronics';
        ```"""
        result = SQLAgent._clean_sql_query(sql)
        expected = "SELECT p.name, p.price FROM querycraft_product p WHERE p.category = 'electronics'"
        self.assertEqual(result, expected)

    def test_with_clause_query(self) -> None:
        """Test cleaning query starting with WITH (CTE)"""
        sql = """WITH customer_orders AS (
            SELECT customer_id, COUNT(*) as count
            FROM querycraft_order
            GROUP BY customer_id
        )
        SELECT * FROM customer_orders"""
        result = SQLAgent._clean_sql_query(sql)
        self.assertTrue(result.startswith("WITH"))
        self.assertIn("customer_orders", result)
        self.assertIn("SELECT * FROM customer_orders", result)

    def test_insert_query(self) -> None:
        """Test cleaning INSERT query"""
        sql = "INSERT INTO querycraft_customer (name, email) VALUES ('John', 'john@example.com')"
        result = SQLAgent._clean_sql_query(sql)
        self.assertTrue(result.startswith("INSERT"))
        self.assertIn("querycraft_customer", result)

    def test_update_query(self) -> None:
        """Test cleaning UPDATE query"""
        sql = "UPDATE querycraft_product SET price = 99.99 WHERE id = 1"
        result = SQLAgent._clean_sql_query(sql)
        self.assertTrue(result.startswith("UPDATE"))
        self.assertIn("querycraft_product", result)

    def test_delete_query(self) -> None:
        """Test cleaning DELETE query"""
        sql = "DELETE FROM querycraft_order WHERE status = 'cancelled'"
        result = SQLAgent._clean_sql_query(sql)
        self.assertTrue(result.startswith("DELETE"))
        self.assertIn("querycraft_order", result)

    def test_case_insensitive_keyword_detection(self) -> None:
        """Test that SQL keywords are detected case-insensitively"""
        sql = "select * from querycraft_customer"
        result = SQLAgent._clean_sql_query(sql)
        self.assertIn("select", result.lower())
        self.assertIn("querycraft_customer", result)

    def test_empty_string(self) -> None:
        """Test handling of empty string"""
        sql = ""
        result = SQLAgent._clean_sql_query(sql)
        self.assertEqual(result, "")

    def test_whitespace_only(self) -> None:
        """Test handling of whitespace-only string"""
        sql = "   \n  \t  "
        result = SQLAgent._clean_sql_query(sql)
        self.assertEqual(result.strip(), "")

    def test_very_short_string(self) -> None:
        """Test that very short strings return original input"""
        sql = "SEL"
        result = SQLAgent._clean_sql_query(sql)
        self.assertEqual(result, "SEL")

    def test_query_with_comments_in_markdown(self) -> None:
        """Test cleaning query that has comments"""
        sql = """```sql
        -- Get all customers
        SELECT * FROM querycraft_customer;
        ```"""
        result = SQLAgent._clean_sql_query(sql)
        self.assertIn("SELECT", result)
        self.assertIn("querycraft_customer", result)

    def test_query_with_leading_whitespace(self) -> None:
        """Test query with significant leading whitespace"""
        sql = "        SELECT id, name FROM querycraft_product"
        result = SQLAgent._clean_sql_query(sql)
        self.assertEqual(result, "SELECT id, name FROM querycraft_product")

    def test_complex_query_with_subquery(self) -> None:
        """Test cleaning a complex query with subqueries"""
        sql = """SELECT c.name
        FROM querycraft_customer c
        WHERE c.id IN (
            SELECT customer_id
            FROM querycraft_order
            WHERE status = 'completed'
        )"""
        result = SQLAgent._clean_sql_query(sql)
        self.assertIn("SELECT c.name FROM querycraft_customer c WHERE c.id IN", result)
        self.assertIn(
            "SELECT customer_id FROM querycraft_order WHERE status = 'completed'",
            result,
        )

    def test_query_with_multiple_markdown_blocks(self) -> None:
        """Test that only the first markdown block is processed"""
        sql = """```sql
        SELECT * FROM querycraft_customer
        ```
        Some explanation here
        ```sql
        SELECT * FROM querycraft_product
        ```"""
        result = SQLAgent._clean_sql_query(sql)
        self.assertIn("querycraft_customer", result)

    def test_llm_response_with_explanation(self) -> None:
        """Test realistic LLM response with explanation and SQL"""
        sql = """Sure! Here's the SQL query to get all customers:

        ```sql
        SELECT id, name, email
        FROM querycraft_customer
        WHERE registration_date >= '2024-01-01';
        ```

        This query will return all customers who registered in 2024."""
        result = SQLAgent._clean_sql_query(sql)
        self.assertEqual(
            result,
            "SELECT id, name, email FROM querycraft_customer WHERE registration_date >= '2024-01-01'",
        )

    def test_query_without_markdown_but_with_prefix_text(self) -> None:
        """Test extraction when SQL is not in markdown but has prefix text"""
        sql = """The query you need is:
        SELECT name, price FROM querycraft_product WHERE category = 'books'"""
        result = SQLAgent._clean_sql_query(sql)
        self.assertEqual(
            result,
            "SELECT name, price FROM querycraft_product WHERE category = 'books'",
        )

    def test_query_with_special_characters(self) -> None:
        """Test query containing special characters in strings"""
        sql = "SELECT * FROM querycraft_customer WHERE email LIKE '%@example.com'"
        result = SQLAgent._clean_sql_query(sql)
        self.assertEqual(
            result, "SELECT * FROM querycraft_customer WHERE email LIKE '%@example.com'"
        )

    def test_query_with_escaped_quotes(self) -> None:
        """Test query with escaped quotes"""
        sql = "SELECT * FROM querycraft_customer WHERE name = 'O''Brien'"
        result = SQLAgent._clean_sql_query(sql)
        self.assertEqual(
            result, "SELECT * FROM querycraft_customer WHERE name = 'O''Brien'"
        )

    def test_multiline_with_line_by_line_extraction(self) -> None:
        """Test line-by-line extraction fallback"""
        sql = """Response:

        SELECT
        c.id,
        c.name
        FROM querycraft_customer c;

        Additional notes"""
        result = SQLAgent._clean_sql_query(sql)
        self.assertEqual("SELECT c.id, c.name FROM querycraft_customer c", result)
