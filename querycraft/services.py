"""
AI Agent service for converting natural language questions to SQL using LangGraph
"""

import logging
from typing import Any, Literal, TypedDict

from django.conf import settings
from django.db import connection
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_ollama import ChatOllama, OllamaLLM
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

# Configure logger for this module
logger = logging.getLogger(__name__)


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
        logger.info("Initializing SQLAgent")
        logger.debug(
            "Ollama configuration - Model: %s, Base URL: %s",
            settings.OLLAMA_MODEL_NAME,
            settings.OLLAMA_BASE_URL,
        )

        # Initialize LangChain Ollama LLM (using OllamaLLM instead of ChatOllama)
        # sqlcoder models work better with completion API rather than chat API
        self.llm = OllamaLLM(
            model=settings.OLLAMA_MODEL_NAME,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.3,
            timeout=60.0,
            num_predict=512,  # Allow up to 512 tokens in response
        )

        # Create prompt template (using PromptTemplate for completion API)
        self.prompt_template = PromptTemplate.from_template(
            """You are a SQL expert who converts natural language questions to precise SQL queries.
Always return only the SQL query without additional explanations.

Database schema:
{schema}

Question: {question}

Return only the SQL query, without additional explanations. Use exact table and column names.
The table names in Django are:
- querycraft_customer (for customers)
- querycraft_product (for products)
- querycraft_order (for orders)

SQL Query:"""
        )

        self.graph = self._build_graph()
        logger.info("SQLAgent initialized successfully with LangGraph workflow")

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
        question = state["question"]
        logger.info("=" * 80)
        logger.info("SQL GENERATION NODE - Starting")
        logger.info("Question: %s", question)

        try:
            schema = self.get_schema_info()
            logger.debug("Retrieved database schema information")

            # Create prompt chain using LangChain
            chain = self.prompt_template | self.llm
            logger.debug("Invoking Ollama LLM for SQL generation...")

            # Log the formatted prompt for debugging
            formatted_prompt_text = self.prompt_template.format(schema=schema, question=question)
            logger.debug("Formatted prompt preview (first 300 chars): %s...", formatted_prompt_text[:300])

            # Invoke the chain
            response = chain.invoke(
                {
                    "schema": schema,
                    "question": question,
                }
            )

            # Log response details for debugging
            logger.debug("Ollama response type: %s", type(response))

            # OllamaLLM returns a string directly
            if isinstance(response, str):
                sql_query = response.strip()
                logger.debug("Response is string type")
            else:
                # Fallback for other types
                sql_query = str(response).strip()
                logger.debug("Response converted to string")

            logger.debug("Raw LLM response (length=%d): '%s'", len(sql_query), sql_query)

            # Check if response is empty
            if not sql_query or len(sql_query) == 0:
                logger.error("Ollama returned empty response!")
                return {
                    **state,
                    "sql_query": None,
                    "error": "Ollama returned empty response. Please check if the model is loaded and responding.",
                    "method": "ollama",
                    "is_valid": False,
                }

            # Clean SQL query
            sql_query = self._clean_sql_query(sql_query)
            logger.info("Generated SQL Query: %s", sql_query)
            logger.info("SQL GENERATION NODE - Completed successfully")

            return {**state, "sql_query": sql_query, "method": "ollama"}
        except Exception as e:
            logger.error("SQL GENERATION NODE - Failed with error: %s", str(e), exc_info=True)
            return {
                **state,
                "sql_query": None,
                "error": f"SQL generation error: {e!s}",
                "method": "ollama",
                "is_valid": False,
            }

    def _node_sql_validator(self, state: GraphState) -> GraphState:
        """Node 2: Validate the generated SQL query"""
        logger.info("=" * 80)
        logger.info("SQL VALIDATION NODE - Starting")
        sql_query = state.get("sql_query")

        if not sql_query:
            logger.warning("No SQL query to validate")
            return {
                **state,
                "is_valid": False,
                "error": state.get("error", "No SQL query generated"),
            }

        logger.debug("Validating SQL query: %s", sql_query)

        # Basic SQL validation
        validation_result = self._validate_sql(sql_query)

        if validation_result.is_valid:
            logger.info("SQL Validation: PASSED ✓")
            logger.info("SQL VALIDATION NODE - Completed successfully")
        else:
            logger.warning("SQL Validation: FAILED ✗")
            logger.warning("Validation error: %s", validation_result.error)
            logger.info("SQL VALIDATION NODE - Completed with validation failure")

        return {
            **state,
            "is_valid": validation_result.is_valid,
            "error": validation_result.error,
        }

    def _node_execute_sql(self, state: GraphState) -> GraphState:
        """Node 3: Execute the validated SQL query"""
        logger.info("=" * 80)
        logger.info("SQL EXECUTION NODE - Starting")
        sql_query = state.get("sql_query")

        if not sql_query:
            logger.error("No SQL query to execute")
            return {**state, "error": "No SQL query to execute"}

        logger.info("Executing SQL: %s", sql_query)

        try:
            with connection.cursor() as cursor:
                cursor.execute(sql_query)
                logger.debug("SQL executed successfully on database")

                # Detect query type
                sql_upper = sql_query.strip().upper()

                if sql_upper.startswith("SELECT"):
                    columns = [col[0] for col in cursor.description] if cursor.description else []
                    rows = cursor.fetchall()

                    # Convert to list of dictionaries
                    results = [dict(zip(columns, row)) for row in rows]

                    logger.info("Query returned %d rows", len(results))
                    logger.info("Columns: %s", columns)
                    logger.debug("Results preview (first 3 rows): %s", results[:3])
                    logger.info("SQL EXECUTION NODE - Completed successfully")

                    return {
                        **state,
                        "results": results,
                        "row_count": len(results),
                        "columns": columns,
                    }
                # For INSERT, UPDATE, DELETE
                logger.info("Query affected %d rows", cursor.rowcount)
                logger.info("SQL EXECUTION NODE - Completed successfully")
                return {
                    **state,
                    "results": [],
                    "row_count": cursor.rowcount,
                    "columns": [],
                }
        except Exception as e:
            logger.error("SQL EXECUTION NODE - Failed with error: %s", str(e), exc_info=True)
            return {**state, "error": f"SQL execution error: {e!s}"}

    def _should_execute(self, state: GraphState) -> Literal["valid", "invalid"]:
        """Conditional function to determine if SQL should be executed"""
        if state.get("is_valid"):
            return "valid"
        return "invalid"

    def _clean_sql_query(self, sql: str) -> str:
        """Clean and extract SQL from model response"""
        logger.debug("Cleaning SQL query. Original length: %d characters", len(sql))
        logger.debug("Original SQL: %s", sql)
        original_sql = sql

        # Remove markdown code blocks if present
        if "```" in sql:
            logger.debug("Detected markdown code block")
            parts = sql.split("```")
            if len(parts) >= 2:
                # Get the content between first pair of ```
                sql = parts[1]
                # Remove language identifier if present
                if sql.strip().lower().startswith(("sql\n", "sql ")):
                    sql = sql.strip()[3:]
                elif sql.strip().upper().startswith(("SQL\n", "SQL ")):
                    sql = sql.strip()[3:]
            sql = sql.strip()
            logger.debug("After removing markdown: %s", sql)

        # Try to find SQL query using multiple strategies
        import re

        # Strategy 1: Look for SELECT/WITH/etc with regex (case-insensitive, allows leading whitespace)
        sql_pattern = r'\b(SELECT|WITH|INSERT|UPDATE|DELETE)\b.*?(?:;|$)'
        match = re.search(sql_pattern, sql, re.IGNORECASE | re.DOTALL)

        if match:
            sql = match.group(0).strip()
            logger.debug("Extracted SQL using regex pattern: %s", sql[:100] if len(sql) > 100 else sql)
        else:
            # Strategy 2: Line-by-line extraction
            logger.debug("Regex pattern didn't match, trying line-by-line extraction")
            lines = sql.split("\n")
            sql_lines = []
            in_sql = False

            for line in lines:
                line_stripped = line.strip()
                # Start collecting when we find SQL keywords
                if re.match(r'^\s*(SELECT|WITH|INSERT|UPDATE|DELETE)\b', line_stripped, re.IGNORECASE):
                    in_sql = True
                    logger.debug("Found SQL start at line: %s", line_stripped)

                if in_sql and line_stripped:
                    sql_lines.append(line_stripped)

                if in_sql and line_stripped.endswith(";"):
                    break

            if sql_lines:
                sql = " ".join(sql_lines).strip()
                logger.debug("After line-by-line extraction: %s", sql[:100] if len(sql) > 100 else sql)
            else:
                # Strategy 3: Use original if no patterns found
                logger.warning("No SQL pattern found, using original cleaned text")
                sql = sql.strip()

        # Remove trailing semicolon if present
        if sql.endswith(";"):
            sql = sql[:-1].strip()

        # Final validation: if still empty or too short, return original
        if not sql or len(sql) < 5:
            logger.error("Cleaning resulted in empty or very short SQL! Using original input")
            result = original_sql.strip()
        else:
            result = sql

        logger.debug("Final cleaned SQL: %s", result)
        return result

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
            return ValidationResult(is_valid=False, error=f"SQL syntax error: {e!s}")

        return ValidationResult(is_valid=True)

    def process_question(self, question: str) -> QueryResult:
        """
        Process a natural language question through the LangGraph workflow

        Returns:
            QueryResult dataclass with success, question, sql_query, results, error, etc.
        """
        logger.info("\n" + "=" * 80)
        logger.info("PROCESS QUESTION - Starting new query processing workflow")
        logger.info("=" * 80)
        logger.info("Input Question: %s", question)

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
            logger.info("Invoking LangGraph workflow...")
            final_state = self.graph.invoke(initial_state)

            logger.info("=" * 80)
            logger.info("WORKFLOW COMPLETED - Processing final state")
            logger.debug("Final state: %s", {k: v for k, v in final_state.items() if k != "results"})

            # Check if we have an error
            if final_state.get("error"):
                logger.error("Workflow completed with error: %s", final_state.get("error"))
                logger.info("Result: FAILURE ✗")
                logger.info("=" * 80 + "\n")
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
                logger.warning("SQL generated but validation failed: %s", final_state.get("error", "Unknown validation error"))
                logger.info("Result: FAILURE ✗")
                logger.info("=" * 80 + "\n")
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
            logger.info("Workflow completed successfully ✓")
            logger.info("SQL Query: %s", final_state.get("sql_query"))
            logger.info("Method: %s", final_state.get("method"))
            logger.info("Rows returned: %d", final_state.get("row_count", 0))
            logger.info("Columns: %s", final_state.get("columns", []))
            logger.info("Result: SUCCESS ✓")
            logger.info("=" * 80 + "\n")
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
            logger.error("Workflow failed with exception: %s", str(e), exc_info=True)
            logger.info("Result: FAILURE ✗")
            logger.info("=" * 80 + "\n")
            return QueryResult(
                success=False,
                question=question,
                sql_query=None,
                method=None,
                error=f"Workflow error: {e!s}",
                results=[],
                row_count=0,
                columns=[],
            )
