"""
AI Agent service for converting natural language questions to SQL using LangGraph
"""

from typing import Any, Literal, TypedDict

from django.conf import settings
from django.db import connection
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field


class GraphState(TypedDict):
    """State for the LangGraph workflow"""

    question: str
    sql_query: str | None
    is_valid: bool | None
    error: str | None
    results: list[dict[str, Any]] | None
    columns: list[str] | None
    row_count: int | None
    method: str | None


class ValidationResult(BaseModel):
    """Result of SQL validation"""

    is_valid: bool
    error: str | None = None


class QueryResult(BaseModel):
    """Result of processing a natural language question"""

    success: bool
    question: str
    sql_query: str | None = None
    method: str | None = None
    results: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    columns: list[str] = Field(default_factory=list)
    error: str | None = None


class SQLAgent:
    """AI agent for converting questions to SQL using LangGraph workflow"""

    def __init__(self):
        # Initialize LangChain Ollama LLM
        self.llm = ChatOllama(
            model=settings.OLLAMA_MODEL_NAME,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.3,
            timeout=60.0,
        )

        # Create prompt template
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a SQL expert who converts natural language questions to precise SQL queries. "
                    "Always return only the SQL query without additional explanations.",
                ),
                (
                    "human",
                    """Convert the following question to a SQL query.

Database schema:
{schema}

Question: {question}

Return only the SQL query, without additional explanations. Use exact table and column names.
The table names in Django are:
- querycraft_customer (for customers)
- querycraft_product (for products)
- querycraft_order (for orders)""",
                ),
            ]
        )

        self.graph = self._build_graph()

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

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph[GraphState, None, GraphState, GraphState](GraphState)

        # Add nodes
        workflow.add_node("sql_generator", self._node_sql_generator)
        workflow.add_node("sql_validator", self._node_sql_validator)
        workflow.add_node("execute_sql", self._node_execute_sql)

        # Define edges
        workflow.set_entry_point("sql_generator")
        workflow.add_edge("sql_generator", "sql_validator")

        # Conditional edge: validator -> execute or end with error
        workflow.add_conditional_edges(
            "sql_validator",
            self._should_execute,
            {"valid": "execute_sql", "invalid": END},
        )

        workflow.add_edge("execute_sql", END)

        return workflow.compile()

    def _node_sql_generator(self, state: GraphState) -> GraphState:
        """Node 1: Generate SQL from natural language question using LangChain Ollama"""
        try:
            schema = self.get_schema_info()
            question = state["question"]

            # Create prompt chain using LangChain
            chain = self.prompt_template | self.llm

            # Invoke the chain
            response = chain.invoke(
                {
                    "schema": schema,
                    "question": question,
                }
            )

            # Extract SQL from response
            sql_query = (
                response.content.strip() if hasattr(response, "content") else str(response).strip()
            )

            # Clean SQL query
            sql_query = self._clean_sql_query(sql_query)

            return {**state, "sql_query": sql_query, "method": "ollama"}
        except Exception as e:
            return {
                **state,
                "sql_query": None,
                "error": f"SQL generation error: {str(e)}",
                "method": "ollama",
                "is_valid": False,
            }

    def _node_sql_validator(self, state: GraphState) -> GraphState:
        """Node 2: Validate the generated SQL query"""
        sql_query = state.get("sql_query")

        if not sql_query:
            return {
                **state,
                "is_valid": False,
                "error": state.get("error", "No SQL query generated"),
            }

        # Basic SQL validation
        validation_result = self._validate_sql(sql_query)

        return {
            **state,
            "is_valid": validation_result.is_valid,
            "error": validation_result.error,
        }

    def _node_execute_sql(self, state: GraphState) -> GraphState:
        """Node 3: Execute the validated SQL query"""
        sql_query = state.get("sql_query")

        if not sql_query:
            return {**state, "error": "No SQL query to execute"}

        try:
            with connection.cursor() as cursor:
                cursor.execute(sql_query)

                # Detect query type
                sql_upper = sql_query.strip().upper()

                if sql_upper.startswith("SELECT"):
                    columns = [col[0] for col in cursor.description] if cursor.description else []
                    rows = cursor.fetchall()

                    # Convert to list of dictionaries
                    results = [dict(zip(columns, row)) for row in rows]

                    return {
                        **state,
                        "results": results,
                        "row_count": len(results),
                        "columns": columns,
                    }
                else:
                    # For INSERT, UPDATE, DELETE
                    return {
                        **state,
                        "results": [],
                        "row_count": cursor.rowcount,
                        "columns": [],
                    }
        except Exception as e:
            return {**state, "error": f"SQL execution error: {str(e)}"}

    def _should_execute(self, state: GraphState) -> Literal["valid", "invalid"]:
        """Conditional function to determine if SQL should be executed"""
        if state.get("is_valid"):
            return "valid"
        return "invalid"

    def _clean_sql_query(self, sql: str) -> str:
        """Clean and extract SQL from model response"""
        # Remove markdown code blocks if present
        if sql.startswith("```"):
            parts = sql.split("```")
            if len(parts) > 1:
                sql = parts[1]
                if sql.startswith("sql"):
                    sql = sql[3:]
            sql = sql.strip()

        # Clean up any extra text before/after SQL
        lines = sql.split("\n")
        sql_lines = []
        in_sql = False
        for line in lines:
            line = line.strip()
            if line.upper().startswith("SELECT") or line.upper().startswith("WITH"):
                in_sql = True
            if in_sql:
                sql_lines.append(line)
            if in_sql and line.endswith(";"):
                break

        if sql_lines:
            sql = " ".join(sql_lines).strip()
            if sql.endswith(";"):
                sql = sql[:-1]

        return sql

    def _validate_sql(self, sql: str) -> ValidationResult:
        """Validate SQL query syntax and safety"""
        sql_upper = sql.strip().upper()

        # Check if SQL is empty
        if not sql or not sql.strip():
            return ValidationResult(is_valid=False, error="Empty SQL query")

        # Only allow SELECT queries for safety
        if not sql_upper.startswith("SELECT"):
            return ValidationResult(is_valid=False, error="Only SELECT queries are allowed")

        # Check for dangerous operations
        dangerous_keywords = [
            "DROP",
            "DELETE",
            "INSERT",
            "UPDATE",
            "ALTER",
            "CREATE",
            "TRUNCATE",
        ]
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return ValidationResult(
                    is_valid=False,
                    error=f"Dangerous operation detected: {keyword} queries are not allowed",
                )

        # Check for valid table names (must reference our tables)
        valid_tables = ["querycraft_customer", "querycraft_product", "querycraft_order"]
        sql_lower = sql.lower()
        has_valid_table = any(table in sql_lower for table in valid_tables)

        if not has_valid_table:
            return ValidationResult(
                is_valid=False,
                error="Query must reference at least one valid table (querycraft_customer, querycraft_product, querycraft_order)",
            )

        # Basic syntax check - try to explain the query (PostgreSQL/SQLite syntax)
        try:
            with connection.cursor() as cursor:
                # Use EXPLAIN to validate syntax without executing
                if connection.vendor == "postgresql":
                    cursor.execute(f"EXPLAIN {sql}")
                elif connection.vendor == "sqlite":
                    # SQLite: Use EXPLAIN QUERY PLAN for validation
                    cursor.execute(f"EXPLAIN QUERY PLAN {sql}")
                else:
                    # For other databases, skip EXPLAIN check
                    pass
        except Exception as e:
            return ValidationResult(is_valid=False, error=f"SQL syntax error: {str(e)}")

        return ValidationResult(is_valid=True)

    def process_question(self, question: str) -> QueryResult:
        """
        Process a natural language question through the LangGraph workflow

        Returns:
            QueryResult dataclass with success, question, sql_query, results, error, etc.
        """
        # Initialize state
        initial_state: GraphState = {
            "question": question,
            "sql_query": None,
            "is_valid": None,
            "error": None,
            "results": None,
            "columns": None,
            "row_count": None,
            "method": None,
        }

        # Run the graph
        try:
            final_state = self.graph.invoke(initial_state)

            # Check if we have an error
            if final_state.get("error"):
                return QueryResult(
                    success=False,
                    question=question,
                    sql_query=final_state.get("sql_query"),
                    method=final_state.get("method"),
                    error=final_state.get("error"),
                    results=[],
                    row_count=0,
                    columns=[],
                )

            # Check if SQL was generated but invalid
            if final_state.get("sql_query") and not final_state.get("is_valid"):
                return QueryResult(
                    success=False,
                    question=question,
                    sql_query=final_state.get("sql_query"),
                    method=final_state.get("method"),
                    error=final_state.get("error", "SQL query validation failed"),
                    results=[],
                    row_count=0,
                    columns=[],
                )

            # Success case
            return QueryResult(
                success=True,
                question=question,
                sql_query=final_state.get("sql_query"),
                method=final_state.get("method"),
                results=final_state.get("results", []),
                row_count=final_state.get("row_count", 0),
                columns=final_state.get("columns", []),
                error=None,
            )
        except Exception as e:
            return QueryResult(
                success=False,
                question=question,
                sql_query=None,
                method=None,
                error=f"Workflow error: {str(e)}",
                results=[],
                row_count=0,
                columns=[],
            )
