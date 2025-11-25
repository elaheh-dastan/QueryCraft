## Prompt Change Issue: Invalid Table Names

We modified the prompt and removed the part that explicitly states that `querycraf_consumer` refers to the consumers table,
relying only on the schema for guidance.

After this change, the model started generating SQL queries using invalid table names, indicating that schema alone wasn’t
sufficient for the model to infer the correct mapping.

To fix the issue, we reverted the prompt to include the explicit explanation,
and the model resumed producing correct queries.

## Missing Read-Only Safeguards Led to Risky Query Execution

Our system currently does not enforce checks to ensure generated queries are read-only.

As a result, the model may occasionally generate destructive SQL queries
(e.g., DELETE, UPDATE, or improperly scoped WHERE clauses).

Without safeguards, these invalid or unintended queries could delete entire tables
or large portions of data.

This highlights the need for adding strict query-type validation or enforcing a SELECT-only
mode before executing model-generated SQL.

## SQL Query Parsing Logic

The `_clean_sql_query` method extracts and cleans SQL queries from model responses, which may include
markdown formatting, explanatory text, or other non-SQL content.

### Parsing Steps

1. **Markdown Code Block Extraction**
   - Detects markdown code blocks (```` ``` ````) in the response
   - Uses regex pattern ````(?:sql)?\s*\n?(.*?)``` ``` to extract content between code fences
   - Handles both ` ```sql\n...``` ` and ` ```...``` ` formats
   - Falls back to splitting on ```` ``` ```` if regex doesn't match
   - Removes language identifier (`sql` or `SQL`) if present after the opening fence

2. **SQL Query Extraction**
   - Uses regex pattern `(SELECT|WITH|INSERT|UPDATE|DELETE).*?(?=;|$)` to find SQL queries
   - Matches from the first SQL keyword (SELECT, WITH, INSERT, UPDATE, DELETE) to the end or semicolon
   - Case-insensitive matching with dot-all mode (handles multi-line queries)
   - Extracts the first matching SQL statement

3. **Trailing Semicolon Removal**
   - Removes trailing semicolons from the extracted query
   - Uses `rstrip(";")` to clean the end of the query

4. **Validation and Fallback**
   - Validates that the cleaned SQL is at least 5 characters long
   - Returns the cleaned SQL if valid
   - Falls back to the original stripped input if cleaning results in invalid/empty SQL

### Design Rationale

The parsing logic prioritizes simplicity and reliability:
- Single-pass regex extraction instead of multiple fallback strategies
- Handles common LLM response formats (markdown code blocks, explanatory text)
- Preserves original input if parsing fails to ensure no data loss
- Minimal validation to avoid over-filtering valid queries


# What if our database grows to 1000 tables
High-Level Solution: Schema Retrieval Before SQL Generation

Instead of sending all schemas:

1. Embed each table & its columns once and store the embeddings.
2. Embed the user query at runtime.
3. Retrieve the top-K relevant tables using vector similarity search.
4. 👉 Send only those tables’ schemas to the LLM to generate SQL.

This makes your system scale from 10 → 10,000 tables easily.

Accuracy increases because irrelevant schemas no longer distract the LLM.

## Advanced Enhancements for Better Accuracy
A. Use a two-stage retrieval

- Retrieve relevant tables.
- Retrieve relevant columns inside those tables.

This reduces prompt size even further.

B. Automatic failed-query fallback

If SQL execution fails:

1. Capture the SQL error
2. Provide error + schema + failed SQL back to the LLM
3. Ask it to fix the query automatically

This solves many real-world issues.


# Known issues
1. We return failure if the query starts with "WITH"
