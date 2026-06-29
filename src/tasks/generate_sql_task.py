from typing import List
from pydantic import BaseModel, Field
from crewai import Task

class SQLAnalystResponse(BaseModel):
    """
    Structured response model for SQL query generation.
    """
    sql_query: str = Field(description="The generated SQLite query. Must use specific columns and default to LIMIT 100.")
    explanation: str = Field(description="A simple plain English explanation of the query.")
    tables_used: List[str] = Field(description="List of database tables used in the query.")
    query_type: str = Field(description="Type of query: SELECT or WRITE.")
    confidence_score: int = Field(description="Confidence score from 0 to 100.")

def create_generate_sql_task(agent, question: str, schema_str: str, follow_up_context: str = "") -> Task:
    """
    Creates and returns the task for generating SQL queries.
    """
    context_instruction = ""
    if follow_up_context:
        context_instruction = (
            f"\nUse the following context from previous queries to resolve pronouns "
            f"or follow up filters:\n{follow_up_context}\n"
        )
        
    description = (
        f"You are given the user's question: '{question}'\n"
        f"{context_instruction}\n"
        f"Here is the database schema:\n"
        f"\"\"\"\n{schema_str}\n\"\"\"\n\n"
        f"Tasks:\n"
        f"1. Analyze the tables and columns. Do not guess names.\n"
        f"2. Write a SQLite query to answer the user's question.\n"
        f"3. Enforce a 'LIMIT 100' clause for all read (SELECT) queries unless the user asks for more.\n"
        f"4. Never write DROP, DELETE, TRUNCATE, or ALTER.\n"
        f"5. Output your analysis using the required JSON format."
    )
    
    return Task(
        description=description,
        expected_output="A structured JSON object matching the SQLAnalystResponse model.",
        agent=agent,
        output_pydantic=SQLAnalystResponse
    )
