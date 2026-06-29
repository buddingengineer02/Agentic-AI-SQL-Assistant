import os
import time
import shutil
from datetime import datetime
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Import utilities and tools
from src.tools.schema_tool import get_db_schema_info, get_db_schema_string
from src.tools.validator import validate_sql
from src.tools.db_executor import execute_read_query, execute_write_query
from src.crew_setup import run_sql_assistant_crew
from src.utils.cost_tracker import calculate_query_cost, log_query_to_file
from src.utils.question_generator import generate_sample_questions
from src.utils.ui_renderer import render_sidebar_schema, get_badge_html, show_cost_and_tokens

load_dotenv()

# Streamlit Page Settings
st.set_page_config(page_title="Agentic SQL Assistant", layout="wide")

# Initialize Session State
if "db_path" not in st.session_state:
    st.session_state.db_path = os.getenv("DATABASE_PATH", "data/sample_db.sqlite")
    st.session_state.last_switched = "Never"
    st.session_state.total_queries = 0
    st.session_state.session_cost_inr = 0.0
    st.session_state.query_history = []
    st.session_state.crew_result = None
    st.session_state.exec_df = None
    st.session_state.exec_msg = ""
    st.session_state.schema_info = get_db_schema_info(st.session_state.db_path)
    st.session_state.sample_questions = generate_sample_questions(st.session_state.schema_info)

# ----------------- SIDEBAR -----------------
st.sidebar.title("🛠️ SQL Assistant Controls")

# Database Switcher
uploaded_file = st.sidebar.file_uploader("Upload SQLite Database", type=["sqlite", "db"])
if uploaded_file is not None:
    target_path = os.path.join("data", uploaded_file.name)
    if st.session_state.db_path != target_path:
        os.makedirs("data", exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.db_path = target_path
        st.session_state.last_switched = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.schema_info = get_db_schema_info(target_path)
        st.session_state.sample_questions = generate_sample_questions(st.session_state.schema_info)
        st.session_state.crew_result = None
        st.session_state.exec_df = None
        st.session_state.exec_msg = ""
        st.toast(f"Database switched to {uploaded_file.name}", icon="✅")

st.sidebar.markdown(f"**Current DB:** `{os.path.basename(st.session_state.db_path)}`  \n*Switched:* {st.session_state.last_switched}")

# Render schema explorer
render_sidebar_schema(st.session_state.schema_info)

# Sample Questions
st.sidebar.markdown("### 💡 Sample Questions")
for sq in st.session_state.sample_questions:
    if st.sidebar.button(sq, key=f"btn_{sq}"):
        st.session_state.query_text = sq
        st.session_state.crew_result = None
        st.session_state.exec_df = None
        st.session_state.exec_msg = ""

# History & Stats
st.sidebar.markdown("### 🕒 Recent History")
for h in st.session_state.query_history[-5:]:
    if st.sidebar.button(f"Q: {h['question'][:25]}...", key=f"hist_{h['timestamp']}"):
        st.session_state.query_text = h["question"]
        st.session_state.crew_result = h["result"]
        st.session_state.exec_df = None
        st.session_state.exec_msg = ""

st.sidebar.markdown("---")
st.sidebar.metric("Queries Executed", st.session_state.total_queries)
st.sidebar.metric("Session API Cost", f"₹{st.session_state.session_cost_inr:.4f}")

# ----------------- MAIN AREA -----------------
st.title("🤖 Agentic AI SQL Assistant")
st.caption("Convert English requests to SQL safely using multi-agent auditing.")

# Input Box
q_input = st.text_input("Ask anything about your database...", key="query_text", placeholder="Show me top 5 products by price")

# Follow up detection
is_followup = any(w in q_input.lower() for w in ["also", "now filter", "same but", "add", "exclude", "sort by", "only show"])
use_context = False
if is_followup and st.session_state.query_history:
    use_context = st.checkbox("This looks like a follow-up. Include previous SQL and result context?", value=True)

if st.button("Generate SQL", type="primary") and q_input:
    st.session_state.exec_df = None
    st.session_state.exec_msg = ""
    with st.spinner("Crew is collaborating..."):
        schema_str = get_db_schema_string(st.session_state.db_path)
        ctx = ""
        if use_context and st.session_state.query_history:
            prev = st.session_state.query_history[-1]
            ctx = f"Previous Query: {prev['question']}\nPrevious SQL: {prev['sql']}"
            
        res = run_sql_assistant_crew(q_input, schema_str, ctx)
        if res.get("error"):
            st.error(res["error"])
        else:
            st.session_state.crew_result = res
            # Track cost
            usage = res["token_usage"]
            _, inr = calculate_query_cost(usage["prompt_tokens"], usage["completion_tokens"])
            st.session_state.session_cost_inr += inr

# Checkpoint details rendering
if st.session_state.crew_result:
    res = st.session_state.crew_result
    analyst = res["analyst_output"]
    compliance = res["compliance_output"]
    sql = analyst.get("sql_query", "")
    
    with st.expander("🔍 Agent 1 (Schema Analyst) Reasoning"):
        st.write(f"**Explanation:** {analyst.get('explanation')}")
        st.write(f"**Tables Identified:** {', '.join(analyst.get('tables_used', []))}")
        
    val_status, val_msg = validate_sql(sql, st.session_state.schema_info)
    with st.expander("🛡️ Python Syntax & Schema Validator Details"):
        val_badge = get_badge_html("PASS", "success") if val_status == "PASS" else get_badge_html("FAIL", "danger")
        st.markdown(f"**Status:** {val_badge}  \n**Message:** {val_msg}", unsafe_allow_html=True)
        
    with st.expander("🔒 Agent 2 (Compliance Guard) Reasoning"):
        st.write(f"**Reason:** {compliance.get('reason')}")
        
    # Checkpoint Header
    st.markdown("### 🚦 Human Checkpoint")
    st.code(sql, language="sql")
    
    # Render Badges
    c_status = compliance.get("status", "REJECTED").upper()
    c_badge = get_badge_html(c_status, "success" if c_status == "APPROVED" else "warning" if c_status == "WARNING" else "danger")
    r_badge = get_badge_html(compliance.get("risk_level", "HIGH"), "success" if compliance.get("risk_level") == "LOW" else "warning" if compliance.get("risk_level") == "MEDIUM" else "danger")
    st.markdown(f"**Compliance Status:** {c_badge} | **Risk Level:** {r_badge} | **Confidence:** `{analyst.get('confidence_score')}%`", unsafe_allow_html=True)
    
    # Cost details
    usd, inr = calculate_query_cost(res["token_usage"]["prompt_tokens"], res["token_usage"]["completion_tokens"])
    show_cost_and_tokens(res["token_usage"], inr, usd)
    
    # Checkpoint Action Buttons
    c1, c2, c3 = st.columns(3)
    if c_status == "APPROVED":
        if c1.button("✅ EXECUTE", type="primary", use_container_width=True):
            df, err = execute_read_query(st.session_state.db_path, sql)
            st.session_state.exec_df = df
            st.session_state.exec_msg = err
            if not err:
                st.session_state.total_queries += 1
                st.session_state.query_history.append({"question": q_input, "sql": sql, "timestamp": time.time(), "result": res})
                log_query_to_file(q_input, sql, res["token_usage"]["prompt_tokens"], res["token_usage"]["completion_tokens"], usd, inr)
        if c2.button("🔄 RETRY", use_container_width=True):
            st.session_state.crew_result = None
            st.rerun()
        if c3.button("❌ ABORT", use_container_width=True):
            st.session_state.crew_result = None
            st.rerun()
            
    elif c_status == "WARNING":
        st.warning("⚠️ This will modify your database. Please confirm you want to proceed.")
        if c1.button("⚠️ EXECUTE WITH WRITE", type="primary", use_container_width=True):
            rows, err = execute_write_query(st.session_state.db_path, sql)
            st.session_state.exec_msg = f"Success. Affected rows: {rows}" if not err else err
            if not err:
                st.session_state.total_queries += 1
                st.session_state.query_history.append({"question": q_input, "sql": sql, "timestamp": time.time(), "result": res})
                log_query_to_file(q_input, sql, res["token_usage"]["prompt_tokens"], res["token_usage"]["completion_tokens"], usd, inr)
        if c2.button("🔄 RETRY", use_container_width=True):
            st.session_state.crew_result = None
            st.rerun()
        if c3.button("❌ ABORT", use_container_width=True):
            st.session_state.crew_result = None
            st.rerun()
            
    else:
        st.error(f"🔴 Blocked: {compliance.get('reason')}")
        if c1.button("❌ ABORT", type="primary", use_container_width=True):
            st.session_state.crew_result = None
            st.rerun()

# Execution Results
import time
if st.session_state.exec_df is not None:
    df = st.session_state.exec_df
    if not df.empty:
        st.markdown("#### 📊 Query Results")
        st.dataframe(df, use_container_width=True)
        st.write(f"**Row Count:** {len(df)} rows")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download as CSV", data=csv, file_name="query_results.csv", mime="text/csv")
    else:
        st.info("Query returned 0 rows.")
elif st.session_state.exec_msg:
    if "Success" in st.session_state.exec_msg:
        st.success(st.session_state.exec_msg)
    else:
        st.error(st.session_state.exec_msg)
