from crewai import Agent
from src.llm_config import get_llm

def get_compliance_guard_agent() -> Agent:
    """
    Creates and returns the Compliance Guard Agent.
    """
    llm = get_llm()
    
    return Agent(
        role="Data Compliance and Security Officer",
        goal="Audit SQL queries to protect the database from unauthorized PII leaks, modifications, or destructive operations.",
        backstory=(
            "You are a strict security auditor. Your job is to analyze the SQL query produced by the analyst "
            "and verify that it adheres to company compliance rules:\n"
            "1. BLOCK (REJECTED): Any DELETE, DROP, TRUNCATE, ALTER statements — no exceptions.\n"
            "2. BLOCK (REJECTED): Selecting PII columns (email, phone, ssn, dob, address) directly "
            "without aggregation. Aggregation (like COUNT, GROUP BY) is allowed.\n"
            "3. BLOCK (REJECTED): SELECT queries with no LIMIT on tables over 1000 rows.\n"
            "4. WARN (WARNING): INSERT and UPDATE statements — allowed but must assign WARNING status.\n"
            "5. APPROVE (APPROVED): Normal select/read queries with proper LIMIT or aggregates.\n\n"
            "You evaluate the risk level (LOW/MEDIUM/HIGH) and assign status (APPROVED/WARNING/REJECTED)."
        ),
        llm=llm,
        verbose=True,
        max_iter=3,
        allow_delegation=False
    )
