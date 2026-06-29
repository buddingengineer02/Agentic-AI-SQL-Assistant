from pydantic import BaseModel, Field
from crewai import Task

class ComplianceResponse(BaseModel):
    """
    Structured response model for SQL compliance auditing.
    """
    status: str = Field(description="Compliance status: APPROVED, WARNING, or REJECTED.")
    reason: str = Field(description="Plain English reason explaining why it was approved, warned, or rejected.")
    risk_level: str = Field(description="Risk level evaluation: LOW, MEDIUM, or HIGH.")
    query_type: str = Field(description="Category of query: READ, WRITE, or DESTRUCTIVE.")

def create_compliance_task(agent, generate_sql_task: Task) -> Task:
    """
    Creates and returns the task for evaluating SQL queries for safety.
    Uses task context chaining to receive the output from the generate_sql_task.
    """
    description = (
        "Analyze the output of the Schema Analyst task (which contains the generated SQL, "
        "explanation, tables used, query type, and confidence score).\n\n"
        "Evaluate the SQL query against compliance rules:\n"
        "- REJECT if it contains DELETE, DROP, TRUNCATE, ALTER.\n"
        "- REJECT if SELECT query has no LIMIT on tables over 1000 rows.\n"
        "- REJECT if it directly selects PII columns (email, phone, ssn, dob, address) without aggregation.\n"
        "- WARN if it is an INSERT or UPDATE query (status = WARNING, query_type = WRITE).\n"
        "- APPROVE if it is a safe read (SELECT) query with proper limit/aggregates (status = APPROVED, query_type = READ).\n\n"
        "Output your evaluation using the required JSON format."
    )
    
    return Task(
        description=description,
        expected_output="A structured JSON object matching the ComplianceResponse model.",
        agent=agent,
        context=[generate_sql_task],  # Direct Task context chaining
        output_pydantic=ComplianceResponse
    )
