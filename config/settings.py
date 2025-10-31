import os
from dotenv import load_dotenv

load_dotenv()

# === KeyCRM API ===
# KeyCRM API key (set in .env)
KEYCRM_API_KEY = os.getenv("KEYCRM_API_KEY", "")

# Base URL for all KeyCRM API requests
API_BASE_URL = "https://openapi.keycrm.app/v1"

# Endpoint for working with cards (pipelines/cards)
API_CARDS_ENDPOINT = "/pipelines/cards"

# Timeout for HTTP requests (seconds)
TIMEOUT = 30

# === Webhook URLs ===
# Production webhook URL (use for live mode)
WEBHOOK_PROD_URL = os.getenv("WEBHOOK_PROD_URL", "")

# Test webhook URL (use for testing)
WEBHOOK_TEST_URL = os.getenv("WEBHOOK_TEST_URL", "")

# === MongoDB Configuration ===
MONGODB_URI = os.getenv("MONGODB_URI", "")

# === Status ID Sets ===
not_qualified_status_ids = {326, 341, 386, 396, 435, 425, 534, 524, 361, 450, 411, 626, 548, 642, 616}
plan_sent_status_ids = {365, 414, 452, 823, 646}
plan_promised_status_ids = {364, 802, 812, 822, 911}
hot_contacts_status_ids = {344, 398, 437, 536, 629, 363, 413, 451, 821, 644, 867, 477}