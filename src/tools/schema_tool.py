import os
from sqlalchemy import create_engine, inspect

def get_db_schema_info(db_path: str) -> dict:
    """
    Inspects the SQLite database using SQLAlchemy and returns a dictionary
    containing tables, columns with their types, primary keys, and foreign keys.
    """
    if not os.path.exists(db_path):
        return {}
        
    # Create engine and inspect
    engine = create_engine(f"sqlite:///{db_path}")
    inspector = inspect(engine)
    
    schema_info = {}
    try:
        tables = inspector.get_table_names()
        for table in tables:
            columns_info = {}
            columns = inspector.get_columns(table)
            for col in columns:
                columns_info[col['name']] = str(col['type'])
                
            pk_constraint = inspector.get_pk_constraint(table)
            primary_keys = pk_constraint.get('constrained_columns', [])
            
            fks = inspector.get_foreign_keys(table)
            foreign_keys = []
            for fk in fks:
                for col, ref_col in zip(fk['constrained_columns'], fk['referred_columns']):
                    foreign_keys.append({
                        "column": col,
                        "referred_table": fk['referred_table'],
                        "referred_column": ref_col
                    })
                    
            schema_info[table] = {
                "columns": columns_info,
                "primary_keys": primary_keys,
                "foreign_keys": foreign_keys
            }
    except Exception as e:
        print(f"Error inspecting database schema: {e}")
    finally:
        engine.dispose()
        
    return schema_info

def get_db_schema_string(db_path: str) -> str:
    """
    Generates a readable schema description text from the database path.
    Used to pass context to the LLM agent.
    """
    schema_info = get_db_schema_info(db_path)
    if not schema_info:
        return "Database is empty or could not be read."
        
    schema_lines = []
    for table_name, details in schema_info.items():
        schema_lines.append(f"Table: {table_name}")
        
        # Columns
        col_strs = []
        for col_name, col_type in details["columns"].items():
            pk_suffix = " (PRIMARY KEY)" if col_name in details["primary_keys"] else ""
            col_strs.append(f"  - {col_name}: {col_type}{pk_suffix}")
        schema_lines.extend(col_strs)
        
        # Foreign Keys
        if details["foreign_keys"]:
            fk_strs = []
            for fk in details["foreign_keys"]:
                fk_strs.append(f"  - FOREIGN KEY ({fk['column']}) REFERENCES {fk['referred_table']}({fk['referred_column']})")
            schema_lines.extend(fk_strs)
            
        schema_lines.append("") # Empty line separator
        
    return "\n".join(schema_lines)
