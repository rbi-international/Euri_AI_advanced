import os
import csv
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv
import logging

load_dotenv()

TOKEN_LOG_PATH = os.getenv("TOKEN_LOG_PATH", "logs/token_usage.csv")
MODEL_COSTS = {
    "gpt-4": 0.03,
    "gpt-3.5": 0.0015,
    "gpt-4.1-nano": 0.0025
}

def get_token_logger():
    os.makedirs(os.path.dirname(TOKEN_LOG_PATH), exist_ok=True)
    logging.basicConfig(
        filename=TOKEN_LOG_PATH.replace(".csv", ".log"),
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s - %(message)s"
    )
    return logging.getLogger("token_utils")

logger = get_token_logger()

# CSV Logging Function
def log_token_usage(model: str, tokens: int = 300):
    try:
        cost_per_1k = MODEL_COSTS.get(model, 0.0025)
        cost = round((tokens / 1000) * cost_per_1k, 6)

        os.makedirs(os.path.dirname(TOKEN_LOG_PATH), exist_ok=True)
        file_exists = os.path.isfile(TOKEN_LOG_PATH)

        with open(TOKEN_LOG_PATH, mode="a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(["Timestamp", "Model", "Tokens", "Cost"])
            writer.writerow([datetime.now().isoformat(), model, tokens, cost])

        logger.info(f"Logged token usage: {model}, Tokens: {tokens}, Cost: ${cost}")
    except Exception as e:
        logger.exception(f"❌ Failed to log token usage: {e}")
        print(f"✅ Logged token usage for model: {model}")

# Optional: Summarize costs for dashboard use
def summarize_token_usage():
    summary = defaultdict(lambda: {"tokens": 0, "cost": 0.0})
    try:
        with open(TOKEN_LOG_PATH, mode="r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                model = row["Model"]
                summary[model]["tokens"] += int(row["Tokens"])
                summary[model]["cost"] += float(row["Cost"])
        return dict(summary)
    except Exception as e:
        logger.exception("❌ Error summarizing token usage")
        return {}

# Future: send to monitoring dashboard
# summary = summarize_token_usage()
# for model, data in summary.items():
#     print(f"Model: {model}, Tokens: {data['tokens']}, Cost: ${data['cost']:.4f}")
