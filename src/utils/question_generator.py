def generate_sample_questions(schema_info: dict) -> list[str]:
    """
    Rule-based generator that inspects the database schema (tables/columns)
    and returns exactly 3 sample questions. Zero LLM cost.
    """
    questions = []
    if not schema_info:
        return [
            "Show me top 5 customers by orders",
            "What is the average price of products?",
            "List all pending orders"
        ]
        
    tables = list(schema_info.keys())
    
    # 1. Simple Select template
    if tables:
        t1 = tables[0]
        questions.append(f"Show me all details of the table {t1}")
        
    # 2. Aggregation/Numeric template
    found_numeric = False
    for table in tables:
        for col_name, col_type in schema_info[table]["columns"].items():
            col_upper = col_type.upper()
            is_num = any(x in col_upper for x in ["INT", "REAL", "FLOAT", "DOUBLE", "NUMERIC"])
            is_num = is_num or col_name.lower() in ["price", "quantity", "amount", "stock_quantity"]
            if is_num and col_name.lower() not in ["id", "product_id", "customer_id", "order_id"]:
                questions.append(f"What is the average {col_name} of {table}?")
                found_numeric = True
                break
        if found_numeric:
            break
            
    if len(questions) < 2 and len(tables) > 1:
        questions.append(f"Show me the total number of {tables[1]}")
        
    # 3. Filtering / Join / Status template
    found_status = False
    for table in tables:
        cols = [c.lower() for c in schema_info[table]["columns"].keys()]
        if "status" in cols:
            questions.append(f"Show me all rows in {table} where status is delivered")
            found_status = True
            break
        elif "city" in cols:
            questions.append(f"List all {table} located in Mumbai")
            found_status = True
            break
            
    if not found_status:
        # Fallback if no specific columns match
        if len(tables) > 1:
            questions.append(f"Show me the top 5 records in {tables[-1]}")
        else:
            questions.append("Show me the total row count of the database")
            
    # Guarantee exactly 3 questions
    while len(questions) < 3:
        questions.append("Show me top 5 customers by orders")
        
    return questions[:3]
