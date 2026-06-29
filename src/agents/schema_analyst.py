from crewai import Agent
from src.llm_config import get_llm

def get_schema_analyst_agent() -> Agent:
    """
    Creates and returns the Database Schema Analyst Agent.
    """
    llm = get_llm()
    
    return Agent(
        role="Database Schema Analyst",
        goal="Convert natural language questions into accurate, valid SQLite SQL queries based on the provided schema.",
        backstory=(
            "You are an expert database administrator and analyst. Your role is to examine "
            "the current database schema structure (tables, columns, types, keys) and translate "
            "the user's natural language question into a precise SQLite query. "
            "You never guess table or column names, always use specific column names instead of SELECT *, "
            "default to SELECT queries, and add LIMIT 100 unless the user asks for all. "
            "You explain your query in plain, easy-to-understand English."
        ),
        llm=llm,
        verbose=True,
        max_iter=3,
        allow_delegation=False
    )
