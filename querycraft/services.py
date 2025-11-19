"""
AI Agent service for converting natural language questions to SQL
"""
import os
import json
import requests
from typing import Dict, Any, Optional
from django.db import connection
from django.conf import settings


class SQLAgent:
    """AI agent for converting questions to SQL"""
    
    def __init__(self):
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')
        self.model_name = 'sqlcoder-7b-2:Q4_K_M'
        self.use_ollama = True  # Always use Ollama in Docker setup
    
    def get_schema_info(self) -> str:
        """Get database schema information"""
        schema_info = """
customers table:
- id (INTEGER, PRIMARY KEY)
- name (VARCHAR)
- email (VARCHAR)
- registration_date (DATE)

products table:
- id (INTEGER, PRIMARY KEY)
- name (VARCHAR)
- category (VARCHAR)
- price (DECIMAL)

orders table:
- id (INTEGER, PRIMARY KEY)
- customer_id (INTEGER, FOREIGN KEY to customers.id)
- product_id (INTEGER, FOREIGN KEY to products.id)
- order_date (DATE)
- quantity (INTEGER)
- status (VARCHAR: 'pending', 'completed', 'cancelled')
"""
        return schema_info
    
    def generate_sql(self, question: str) -> Dict[str, Any]:
        """
        Convert natural language question to SQL
        Uses Ollama for LLM inference
        """
        if self.use_ollama:
            return self._generate_sql_with_ollama(question)
        else:
            return self._generate_sql_simple(question)
    
    def _generate_sql_with_ollama(self, question: str) -> Dict[str, Any]:
        """Use Ollama to generate SQL"""
        try:
            schema = self.get_schema_info()
            
            prompt = f"""You are a SQL expert. Convert the following question to a SQL query.

Database schema:
{schema}

Question: {question}

Return only the SQL query, without additional explanations. Use exact table and column names. The table names in Django are:
- querycraft_customer (for customers)
- querycraft_product (for products)
- querycraft_order (for orders)"""
            
            # Call Ollama API
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                    }
                },
                timeout=60
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            sql_query = result.get('response', '').strip()
            
            # Remove markdown code blocks if present
            if sql_query.startswith("```"):
                parts = sql_query.split("```")
                if len(parts) > 1:
                    sql_query = parts[1]
                    if sql_query.startswith("sql"):
                        sql_query = sql_query[3:]
                sql_query = sql_query.strip()
            
            # Clean up any extra text before/after SQL
            lines = sql_query.split('\n')
            sql_lines = []
            in_sql = False
            for line in lines:
                line = line.strip()
                if line.upper().startswith('SELECT') or line.upper().startswith('WITH'):
                    in_sql = True
                if in_sql:
                    sql_lines.append(line)
                if in_sql and line.endswith(';'):
                    break
            
            if sql_lines:
                sql_query = ' '.join(sql_lines).strip()
                if sql_query.endswith(';'):
                    sql_query = sql_query[:-1]
            
            return {
                'sql': sql_query,
                'method': 'ollama'
            }
        except requests.exceptions.RequestException as e:
            return {
                'sql': None,
                'error': f"Ollama connection error: {str(e)}",
                'method': 'ollama'
            }
        except Exception as e:
            return {
                'sql': None,
                'error': str(e),
                'method': 'ollama'
            }
    
    def _generate_sql_simple(self, question: str) -> Dict[str, Any]:
        """Simple system for converting common questions to SQL (no API required)"""
        question_lower = question.lower()
        
        # Simple patterns for conversion
        patterns = {
            'user': 'users',
            'users': 'users',
            'order': 'orders',
            'orders': 'orders',
            'last month': "datetime('now', '-1 month')",
            'past month': "datetime('now', '-1 month')",
            'last week': "datetime('now', '-7 days')",
            'past week': "datetime('now', '-7 days')",
            'last day': "datetime('now', '-1 day')",
            'yesterday': "datetime('now', '-1 day')",
        }
        
        # Simple conversions
        if 'how many customers' in question_lower or 'number of customers' in question_lower or 'count customers' in question_lower:
            if 'last month' in question_lower or 'past month' in question_lower:
                return {
                    'sql': "SELECT COUNT(*) FROM querycraft_customer WHERE registration_date >= date('now', '-1 month')",
                    'method': 'simple_pattern'
                }
            else:
                return {
                    'sql': "SELECT COUNT(*) FROM querycraft_customer",
                    'method': 'simple_pattern'
                }
        
        elif 'new customers' in question_lower or 'new customer' in question_lower:
            if 'last month' in question_lower or 'past month' in question_lower:
                return {
                    'sql': "SELECT COUNT(*) FROM querycraft_customer WHERE registration_date >= date('now', '-1 month')",
                    'method': 'simple_pattern'
                }
            else:
                return {
                    'sql': "SELECT COUNT(*) FROM querycraft_customer",
                    'method': 'simple_pattern'
                }
        
        elif 'all customers' in question_lower or 'list customers' in question_lower or 'show customers' in question_lower:
            return {
                'sql': "SELECT * FROM querycraft_customer ORDER BY registration_date DESC",
                'method': 'simple_pattern'
            }
        
        elif 'products' in question_lower or 'product' in question_lower:
            if 'count' in question_lower or 'how many' in question_lower or 'number' in question_lower:
                return {
                    'sql': "SELECT COUNT(*) FROM querycraft_product",
                    'method': 'simple_pattern'
                }
            else:
                return {
                    'sql': "SELECT * FROM querycraft_product ORDER BY name",
                    'method': 'simple_pattern'
                }
        
        elif 'order' in question_lower:
            if 'count' in question_lower or 'how many' in question_lower or 'number' in question_lower:
                return {
                    'sql': "SELECT COUNT(*) FROM querycraft_order",
                    'method': 'simple_pattern'
                }
            else:
                return {
                    'sql': "SELECT * FROM querycraft_order ORDER BY order_date DESC LIMIT 10",
                    'method': 'simple_pattern'
                }
        
        # Default: return customer count
        return {
            'sql': "SELECT COUNT(*) FROM querycraft_customer",
            'method': 'simple_pattern',
            'note': 'For better results, ensure Ollama service is running'
        }
    
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute SQL query and return results"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                
                # Detect query type
                sql_upper = sql.strip().upper()
                
                if sql_upper.startswith('SELECT'):
                    columns = [col[0] for col in cursor.description] if cursor.description else []
                    rows = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    results = [dict(zip(columns, row)) for row in rows]
                    
                    return {
                        'success': True,
                        'results': results,
                        'row_count': len(results),
                        'columns': columns
                    }
                else:
                    # For INSERT, UPDATE, DELETE
                    return {
                        'success': True,
                        'message': 'Query executed successfully',
                        'rows_affected': cursor.rowcount
                    }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

