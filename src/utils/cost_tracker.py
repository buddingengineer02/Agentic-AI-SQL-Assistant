import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Gemini 1.5 Flash-Lite pricing (Free API has limits but we still track costs as requested)
# Input: $0.075 per 1M tokens ($0.000000075 per token)
# Output: $0.30 per 1M tokens ($0.0000003 per token)
INPUT_RATE_USD = 0.075 / 1_000_000
OUTPUT_RATE_USD = 0.30 / 1_000_000
USD_TO_INR = float(os.getenv("USD_TO_INR", 84.0))

def calculate_query_cost(input_tokens: int, output_tokens: int) -> tuple[float, float]:
    """
    Calculates query cost based on token counts.
    Returns: (cost_usd, cost_inr)
    """
    usd_cost = (input_tokens * INPUT_RATE_USD) + (output_tokens * OUTPUT_RATE_USD)
    inr_cost = usd_cost * USD_TO_INR
    return usd_cost, inr_cost

def log_query_to_file(question: str, sql_query: str, input_tokens: int, output_tokens: int, usd_cost: float, inr_cost: float):
    """
    Appends query details, token counts, and cost details to queries_log.txt.
    """
    log_file = "queries_log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = (
        f"=== {timestamp} ===\n"
        f"Question: {question}\n"
        f"SQL: {sql_query.strip()}\n"
        f"Input Tokens: {input_tokens} | Output Tokens: {output_tokens}\n"
        f"Cost USD: ${usd_cost:.6f} | Cost INR: \u20b9{inr_cost:.4f}\n"
        f"--------------------------------------------------\n"
    )
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Error writing to query log: {e}")
