import re
import sqlparse
from sqlparse.tokens import Keyword, Name

def extract_tables_and_columns(parsed):
    """
    Traverses the sqlparse AST to extract table names and column names/references,
    as well as aliases defined using 'AS'.
    """
    tables = set()
    columns = set()
    aliases = set()
    
    # Simple regex to find words that follow FROM/JOIN or are column references
    # we convert SQL to lowercase to make checking robust
    tokens = []
    
    def walk(token_list):
        for token in token_list:
            if token.is_group:
                walk(token)
            else:
                tokens.append(token)
                
    walk(parsed)
    
    # Pass 1: Find aliases defined via 'AS <alias>'
    for i, token in enumerate(tokens):
        if token.ttype == Keyword and token.value.upper() == 'AS':
            # Look ahead for next Name token
            for j in range(i + 1, min(i + 5, len(tokens))):
                if tokens[j].ttype == Name:
                    aliases.add(tokens[j].value.lower())
                    break
                    
    # Pass 2: Extract tables and columns
    # We find tables by looking for tokens after FROM or JOIN
    for i, token in enumerate(tokens):
        if token.ttype == Keyword and token.value.upper() in ('FROM', 'JOIN'):
            # Find the next Name token which represents the table
            for j in range(i + 1, min(i + 8, len(tokens))):
                if tokens[j].ttype == Name:
                    tables.add(tokens[j].value.lower())
                    break
        elif token.ttype == Name:
            val = token.value.lower()
            # If it's a dotted name (e.g. t.column_name), split it
            if '.' in val:
                parts = val.split('.')
                # Left side could be table or alias
                # Right side is the column
                columns.add(parts[-1])
            else:
                columns.add(val)
                
    return tables, columns, aliases

def validate_sql(sql_query: str, schema_info: dict) -> tuple[str, str]:
    """
    Validates a generated SQL query against the schema and safety guidelines.
    Returns: (status, message) where status is "PASS" or "FAIL".
    """
    if not sql_query or not sql_query.strip():
        return "FAIL", "SQL query is empty."
        
    # 1. Check SQL syntax using sqlparse
    try:
        parsed_statements = sqlparse.parse(sql_query)
        if not parsed_statements:
            return "FAIL", "SQL Syntax check failed: Could not parse statement."
        parsed = parsed_statements[0]
    except Exception as e:
        return "FAIL", f"SQL Syntax parse error: {e}"
        
    query_upper = sql_query.upper().strip()
    is_select = query_upper.startswith("SELECT")
    
    # 2. Check dangerous keywords for SELECT queries
    if is_select:
        dangerous_keywords = ["DELETE", "DROP", "TRUNCATE", "ALTER", "GRANT", "REVOKE"]
        for kw in dangerous_keywords:
            if re.search(r'\b' + kw + r'\b', query_upper):
                return "FAIL", f"Dangerous keyword '{kw}' detected in read query."
                
        # 3. Check that LIMIT is present for SELECT queries
        if "LIMIT" not in query_upper:
            return "FAIL", "SELECT queries must contain a LIMIT clause for safety."
            
    # 4. Extract referenced tables and columns
    ref_tables, ref_columns, aliases = extract_tables_and_columns(parsed)
    
    # List of valid items in schema
    valid_tables = {t.lower() for t in schema_info.keys()}
    valid_columns = set()
    for t_info in schema_info.values():
        for col in t_info["columns"].keys():
            valid_columns.add(col.lower())
            
    # Common SQL functions and keywords to ignore when checking columns
    ignored_words = {
        "count", "sum", "avg", "min", "max", "coalesce", "date", "strftime",
        "now", "null", "as", "select", "from", "where", "join", "on", "and", 
        "or", "group", "by", "order", "limit", "offset", "desc", "asc", "having",
        "case", "when", "then", "else", "end", "in", "like", "not", "is", "between"
    }
    
    # Verify tables exist
    for t in ref_tables:
        if t not in valid_tables:
            return "FAIL", f"Table '{t}' does not exist in the database schema."
            
    # Verify columns exist (excluding aliases, tables, and SQL keywords)
    for c in ref_columns:
        if c in valid_columns or c in valid_tables or c in aliases or c in ignored_words:
            continue
        # Also check if it's a numeric constant or wildcard
        if c.isdigit() or c == "*":
            continue
        return "FAIL", f"Column '{c}' does not exist in the database schema."
        
    return "PASS", "SQL validated successfully."
