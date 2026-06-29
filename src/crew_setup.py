import re
import json
from crewai import Crew, Process
from src.agents.schema_analyst import get_schema_analyst_agent
from src.agents.compliance_guard import get_compliance_guard_agent
from src.tasks.generate_sql_task import create_generate_sql_task, SQLAnalystResponse
from src.tasks.compliance_task import create_compliance_task, ComplianceResponse
from src.utils.logger import logger

def clean_and_parse_json(text: str) -> dict | None:
    """
    Attempts to extract and parse JSON from a raw string, handling markdown code blocks.
    """
    if not text:
        return None
    # Look for ```json ... ``` blocks
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    json_str = match.group(1).strip() if match else text.strip()
    try:
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"Manual JSON parsing failed: {e}. Raw content: {text}")
        return None

def run_sql_assistant_crew(question: str, schema_str: str, follow_up_context: str = "") -> dict:
    """
    Runs the CrewAI pipeline to generate and audit a SQL query.
    Returns: a dict with analyst_output, compliance_output, token_usage, and error (if any).
    """
    try:
        # Instantiate agents
        analyst_agent = get_schema_analyst_agent()
        compliance_agent = get_compliance_guard_agent()
        
        # Create tasks (context chaining enabled)
        sql_task = create_generate_sql_task(analyst_agent, question, schema_str, follow_up_context)
        safety_task = create_compliance_task(compliance_agent, sql_task)
        
        # Configure crew
        crew = Crew(
            agents=[analyst_agent, compliance_agent],
            tasks=[sql_task, safety_task],
            process=Process.sequential,
            verbose=True
        )
        
        logger.info(f"Kicking off SQL Assistant Crew for question: '{question}'")
        try:
            crew_output = crew.kickoff()
        except Exception as e:
            err_str = str(e)
            is_rate_limit = any(term in err_str for term in ["429", "ResourceExhausted", "Quota exceeded", "rate limit"])
            if is_rate_limit:
                msg = "Rate limit hit, retrying in 12 seconds..."
                logger.warning(msg)
                import time
                import streamlit as st
                try:
                    st.warning(msg)
                except Exception:
                    pass
                time.sleep(12)
                crew_output = crew.kickoff()
            else:
                raise e
        
        # 1. Parse Analyst Output
        analyst_pydantic = sql_task.output.pydantic
        if analyst_pydantic:
            analyst_data = {
                "sql_query": analyst_pydantic.sql_query,
                "explanation": analyst_pydantic.explanation,
                "tables_used": analyst_pydantic.tables_used,
                "query_type": analyst_pydantic.query_type,
                "confidence_score": analyst_pydantic.confidence_score
            }
        else:
            # Fallback to manual parsing
            parsed_json = clean_and_parse_json(sql_task.output.raw)
            if parsed_json:
                analyst_data = {
                    "sql_query": parsed_json.get("sql_query", ""),
                    "explanation": parsed_json.get("explanation", ""),
                    "tables_used": parsed_json.get("tables_used", []),
                    "query_type": parsed_json.get("query_type", "SELECT"),
                    "confidence_score": int(parsed_json.get("confidence_score", 50))
                }
            else:
                raise ValueError("Could not parse Schema Analyst output.")
                
        # 2. Parse Compliance Output
        compliance_pydantic = safety_task.output.pydantic
        if compliance_pydantic:
            compliance_data = {
                "status": compliance_pydantic.status,
                "reason": compliance_pydantic.reason,
                "risk_level": compliance_pydantic.risk_level,
                "query_type": compliance_pydantic.query_type
            }
        else:
            parsed_json = clean_and_parse_json(safety_task.output.raw)
            if parsed_json:
                compliance_data = {
                    "status": parsed_json.get("status", "REJECTED"),
                    "reason": parsed_json.get("reason", "Failed to parse compliance output."),
                    "risk_level": parsed_json.get("risk_level", "HIGH"),
                    "query_type": parsed_json.get("query_type", "READ")
                }
            else:
                compliance_data = {
                    "status": "REJECTED",
                    "reason": "Failed to parse security audit results.",
                    "risk_level": "HIGH",
                    "query_type": "READ"
                }
                
        # 3. Retrieve token usage metrics
        usage = crew.usage_metrics
        if usage:
            token_usage = {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                "completion_tokens": getattr(usage, "completion_tokens", 0),
                "total_tokens": getattr(usage, "total_tokens", 0)
            }
        else:
            token_usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        
        return {
            "analyst_output": analyst_data,
            "compliance_output": compliance_data,
            "token_usage": token_usage,
            "error": ""
        }
        
    except Exception as e:
        logger.error(f"Error in CrewAI pipeline execution: {e}")
        return {
            "analyst_output": {},
            "compliance_output": {},
            "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "error": f"Orchestration failure: {str(e)}"
        }
