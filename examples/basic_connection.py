"""
Example: connect to your panel and list all inbounds.

This is the simplest possible xuipy script - a good first thing to run
to confirm your panel URL and credentials are correct.
"""
from xuipy.client import XUI

# Fill in your own panel details here
xui = XUI(
    base_url="https://your-panel-url.com",
    username="admin",
    password="admin",
)

# get_inbounds() returns a plain list of dicts - one per inbound
inbounds = xui.get_inbounds()

print(f"Connected! Found {len(inbounds)} inbound(s):\n")
for inbound in inbounds:
    print(f"- {inbound['remark']}")
    print(f"    id: {inbound['id']}")
    print(f"    port: {inbound['port']}")
    print(f"    protocol: {inbound['protocol']}")
    print(f"    enabled: {inbound['enable']}")
    print()