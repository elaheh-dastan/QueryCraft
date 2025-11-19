"""
AI Agent service for converting natural language questions to SQL
"""
import os
import json
from typing import Dict, Any, Optional
from django.db import connection
from django.conf import settings


class SQLAgent:
    """AI agent for converting questions to SQL"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.use_openai = self.api_key is not None
    
    def get_schema_info(self) -> str:
        """Get database schema information"""
        schema_info = """
users table:
- id (INTEGER, PRIMARY KEY)
- username (VARCHAR, UNIQUE)
- email (VARCHAR)
- created_at (DATETIME)
- is_active (BOOLEAN)

orders table:
- id (INTEGER, PRIMARY KEY)
- user_id (INTEGER, FOREIGN KEY to users.id)
- total_amount (DECIMAL)
- created_at (DATETIME)
- status (VARCHAR: 'pending', 'completed', 'cancelled')
"""
        return schema_info
    
    def generate_sql(self, question: str) -> Dict[str, Any]:
        """
        Convert natural language question to SQL
        Uses a simple system if OpenAI API Key is not available
        """
        if self.use_openai:
            return self._generate_sql_with_openai(question)
        else:
            return self._generate_sql_simple(question)
    
    def _generate_sql_with_openai(self, question: str) -> Dict[str, Any]:
        """Use OpenAI to generate SQL"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            
            schema = self.get_schema_info()
            
            prompt = f"""You are a SQL expert. Convert the following question to a SQL query.

Database schema:
{schema}

Question: {question}

Return only the SQL query, without additional explanations. Use exact table and column names."""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a SQL expert who converts questions to precise SQL queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if sql_query.startswith("```"):
                sql_query = sql_query.split("```")[1]
                if sql_query.startswith("sql"):
                    sql_query = sql_query[3:]
                sql_query = sql_query.strip()
            
            return {
                'sql': sql_query,
                'method': 'openai'
            }
        except Exception as e:
            return {
                'sql': None,
                'error': str(e),
                'method': 'openai'
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
        if 'how many users' in question_lower or 'number of users' in question_lower or 'count users' in question_lower:
            if 'last month' in question_lower or 'past month' in question_lower:
                return {
                    'sql': "SELECT COUNT(*) FROM querycraft_user WHERE created_at >= datetime('now', '-1 month')",
                    'method': 'simple_pattern'
                }
            else:
                return {
                    'sql': "SELECT COUNT(*) FROM querycraft_user",
                    'method': 'simple_pattern'
                }
        
        elif 'new users' in question_lower or 'new user' in question_lower:
            if 'last month' in question_lower or 'past month' in question_lower:
                return {
                    'sql': "SELECT COUNT(*) FROM querycraft_user WHERE created_at >= datetime('now', '-1 month')",
                    'method': 'simple_pattern'
                }
            else:
                return {
                    'sql': "SELECT COUNT(*) FROM querycraft_user",
                    'method': 'simple_pattern'
                }
        
        elif 'all users' in question_lower or 'list users' in question_lower or 'show users' in question_lower:
            return {
                'sql': "SELECT * FROM querycraft_user ORDER BY created_at DESC",
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
                    'sql': "SELECT * FROM querycraft_order ORDER BY created_at DESC LIMIT 10",
                    'method': 'simple_pattern'
                }
        
        # Default: return user count
        return {
            'sql': "SELECT COUNT(*) FROM querycraft_user",
            'method': 'simple_pattern',
            'note': 'For better results, please set OPENAI_API_KEY'
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

