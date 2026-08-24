"""
Example: create a client, get their links, check traffic,
update their quota, then delete them.
"""
from xuipy.client import XUI

xui = XUI(
    base_url="https://your-panel-url.com",
    username="admin",
    password="admin",
)

CLIENT_EMAIL = "demo-user"

print("Connected to panel\n")

# --- Create a client ---
# If inbound_ids is omitted, the client is attached to all current inbounds.
# Here we attach to just the first inbound instead.
inbounds = xui.get_inbounds()
first_inbound_id = inbounds[0]["id"]

xui.add_client(
    email=CLIENT_EMAIL,
    inbound_ids=[first_inbound_id],
    expiry_days=30,   # expires 30 days from now, 0 = never
    total_gb=10,      # 10 GB quota, 0 = unlimited
)
print(f"Created client '{CLIENT_EMAIL}'")

# --- Get their individual proxy links (vless://, vmess://, etc.) ---
links = xui.get_client_links(CLIENT_EMAIL)
print("\nConnection links:")
for i, link in enumerate(links, 1):
    print(f"\n[{i}] {link}")
    
# --- Build their subscription link using the panel's own subURI setting ---
client_data = xui.get_client(CLIENT_EMAIL)
sub_id = client_data["client"]["subId"]

settings = xui.get_all_settings()
sub_uri = settings["subURI"]  # e.g. "your-host.com:2096/sub/"

subscription_url = f"https://{sub_uri}{sub_id}"
print(f"\nSubscription URL: {subscription_url}")

# --- Check traffic usage ---
traffic = xui.get_client_traffic(CLIENT_EMAIL)
used_mb = (traffic["up"] + traffic["down"]) / (1024 * 1024)
print(f"\nTraffic used so far: {used_mb:.2f} MB")

# --- Update their quota ---
xui.update_client(CLIENT_EMAIL, total_gb=20)
print("Updated quota to 20 GB")

# --- Clean up ---
xui.delete_client(CLIENT_EMAIL)
print(f"Deleted '{CLIENT_EMAIL}'")

print("\nDone.")