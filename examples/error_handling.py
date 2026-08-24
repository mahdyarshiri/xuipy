"""
Example: xuipy's exception types and how to handle each one.

This script deliberately triggers each kind of failure on purpose,
just to show what happens - it's meant to be read, not just run.
"""
from xuipy.client import XUI
from xuipy.exceptions import XUIError, XUIAuthError, XUIRequestError, XUIValidationError

# --- XUIValidationError: caught locally, no request is ever sent ---
# Good for catching obviously-bad input fast, without waiting on the network.
try:
    XUI(base_url="")  # empty base_url is invalid
except XUIValidationError as e:
    print(f"Validation error (no request sent): {e}")

# --- XUIAuthError: the panel rejected your login/credentials ---
try:
    XUI(
        base_url="https://your-panel-url.com",
        username="admin",
        password="definitely-wrong-password",
    )
except XUIAuthError as e:
    print(f"Auth error: {e}")

# --- XUIRequestError: a normal request failed for some other reason ---
xui = XUI(
    base_url="https://your-panel-url.com",
    username="admin",
    password="admin",
)

try:
    xui.get_inbound(999999)  # an id that almost certainly doesn't exist
except XUIRequestError as e:
    print(f"Request error: {e}")

# --- XUIError: the base class - catches ANY of the above at once ---
# Use this when you don't care which specific thing went wrong.
try:
    xui.get_client("a-user-that-does-not-exist")
except XUIError as e:
    print(f"Something went wrong: {e}")