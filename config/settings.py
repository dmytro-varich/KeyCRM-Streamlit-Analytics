import os
from dotenv import load_dotenv

load_dotenv()

# === KeyCRM API ===
# KeyCRM API key (set in .env)
KEYCRM_API_KEY = os.getenv("KEYCRM_API_KEY", "your_api_key_here")

# Base URL for all KeyCRM API requests
API_BASE_URL = "https://openapi.keycrm.app/v1"

# Endpoint for working with cards (pipelines/cards)
API_CARDS_ENDPOINT = "/pipelines/cards"

# Timeout for HTTP requests (seconds)
TIMEOUT = 30

# === Webhook URLs ===
# Production webhook URL (use for live mode)
WEBHOOK_PROD_URL = "https://primary-production-76c7.up.railway.app/webhook/get-keycrm-today"

# Test webhook URL (use for testing)
WEBHOOK_TEST_URL = "https://primary-production-76c7.up.railway.app/webhook-test/get-keycrm-today"
