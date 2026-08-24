"""
Example: create an inbound, rename it, toggle it on/off, then delete it.

Shows the basic create -> update -> delete lifecycle for inbounds.
"""
from xuipy.client import XUI

xui = XUI(
    base_url="https://your-panel-url.com",
    username="admin",
    password="admin",
)

# --- Create a new VLESS inbound ---
# add_inbound() takes a dict describing the inbound - the shape mirrors
# what x-ui's own API expects (protocol, port, settings, streamSettings, sniffing).
new_inbound = {
    "remark": "my-new-inbound",
    "protocol": "vless",
    "port": 20000,
    "enable": True,
    "expiryTime": 0,
    "settings": {
        "clients": [],
        "decryption": "none",
    },
    "streamSettings": {
        "network": "tcp",
        "security": "none",
    },
    "sniffing": {
        "enabled": True,
        "destOverride": ["http", "tls", "quic", "fakedns"],
    },
}

created = xui.add_inbound(new_inbound)
inbound_id = created["id"]
print(f"Created inbound '{created['remark']}' with id {inbound_id}")

# --- Rename it ---
new_inbound["remark"] = "my-renamed-inbound"
xui.update_inbound(inbound_id, new_inbound)
print("Renamed the inbound")

# --- Turn it off, then back on ---
xui.set_inbound_enable(inbound_id, False)
print("Disabled the inbound")

xui.set_inbound_enable(inbound_id, True)
print("Re-enabled the inbound")

# --- Delete it ---
xui.delete_inbound(inbound_id)
print(f"Deleted inbound {inbound_id}")