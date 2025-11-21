## Prompt Change Issue: Invalid Table Names

We modified the prompt and removed the part that explicitly states that `querycraf_consumer` refers to the consumers table,
relying only on the schema for guidance.

After this change, the model started generating SQL queries using invalid table names, indicating that schema alone wasn’t
sufficient for the model to infer the correct mapping.

To fix the issue, we reverted the prompt to include the explicit explanation,
and the model resumed producing correct queries.