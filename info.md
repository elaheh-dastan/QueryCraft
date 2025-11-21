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