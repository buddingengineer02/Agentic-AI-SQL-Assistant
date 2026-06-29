import streamlit as st

def render_sidebar_schema(schema_info: dict):
    """
    Renders the database schema in the sidebar with expandable tables
    and column type details.
    """
    st.sidebar.markdown("### 🗃️ Database Schema")
    if not schema_info:
        st.sidebar.info("No tables found in database.")
        return
        
    for table_name, details in schema_info.items():
        with st.sidebar.expander(f"📋 {table_name}"):
            for col, col_type in details["columns"].items():
                pk_indicator = "🔑 " if col in details["primary_keys"] else "🔹 "
                st.write(f"{pk_indicator}**{col}**: `{col_type}`")
                
            # Render foreign key relations if any
            if details.get("foreign_keys"):
                st.write("---")
                st.write("**Relations:**")
                for fk in details["foreign_keys"]:
                    st.caption(f"🔗 `{fk['column']}` ➡️ `{fk['referred_table']}.{fk['referred_column']}`")

def get_badge_html(label: str, style_type: str) -> str:
    """
    Generates a beautiful HTML badge for the UI.
    """
    colors = {
        "success": ("#d4edda", "#155724"),
        "warning": ("#fff3cd", "#856404"),
        "danger": ("#f8d7da", "#721c24"),
        "info": ("#cce5ff", "#004085"),
        "gray": ("#e2e3e5", "#383d41")
    }
    bg, fg = colors.get(style_type, colors["gray"])
    return f"""
    <span style="
        background-color: {bg};
        color: {fg};
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: bold;
        display: inline-block;
        border: 1px solid {fg}40;
    ">{label}</span>
    """

def show_cost_and_tokens(tokens_dict: dict, inr_cost: float, usd_cost: float):
    """
    Renders token usage and cost badges.
    """
    st.markdown("##### 🪙 Cost and Token Usage")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Tokens:** {tokens_dict.get('total_tokens', 0)} (Total)")
        st.caption(f"In: {tokens_dict.get('prompt_tokens', 0)} | Out: {tokens_dict.get('completion_tokens', 0)}")
    with col2:
        st.markdown(f"**Cost (USD):** `${usd_cost:.6f}`")
    with col3:
        st.markdown(f"**Cost (INR):** `\u20b9{inr_cost:.4f}`")
