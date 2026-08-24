"""
Example: create an API token, then connect using the token instead of
a username and password. Useful for bots, scripts, and CI where you
don't want to store an admin password.
"""
from xuipy.client import XUI

# Step 1: connect normally (username/password) to create the token
xui = XUI(
    base_url="https://your-panel-url.com",
    username="admin",
    password="admin",
)

token_info = xui.create_api_token("my-bot-token")
token = token_info["token"]

print(f"Created token: {token}")
print("Copy this now - the panel will never show it again.\n")

# Step 2: connect again, this time using ONLY the token
bot_xui = XUI(
    base_url="https://your-panel-url.com",
    api_token=token,
)

inbounds = bot_xui.get_inbounds()
print(f"Connected via API token. Found {len(inbounds)} inbound(s).")

# --- Clean up: disable then delete the token when you're done with it ---
xui.set_api_token_enabled(token_info["id"], False)
xui.delete_api_token(token_info["id"])
print("Token revoked")