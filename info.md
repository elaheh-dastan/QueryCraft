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