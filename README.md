# xuipy


A Python client for the [3x-ui](https://github.com/MHSanaei/3x-ui) panel API, covering inbounds, clients, and server management.

## Installing

```bash
pip install xuipy
```

## Quick start

```python
from xuipy import XUI

xui = XUI(
    base_url="https://your-panel-url.com",
    username="admin",
    password="admin",
)

for client in xui.get_clients():
    print(client["email"])
```

## Authentication

**Username and password:**

```python
xui = XUI(base_url="https://your-panel-url.com", username="admin", password="admin")
```

### Base URL

Use the exact address you use to access your panel in a browser, including port and any custom base path:

```
https://your-panel-url.com
https://your-panel-url.com:2053
```

**API token** — useful when you don't want to store an admin password:

```python
xui = XUI(base_url="https://your-panel-url.com", api_token="your-token-here")
```

You can get a token from the panel UI under **Settings → Security → API Token**, or generate one from code:

```python
token = xui.create_api_token("my-bot-token")
print(token["token"])  # shown only once — save it now
```


## Usage

### Inbounds

```python
xui.get_inbounds()                  # list every inbound
xui.get_inbound(1)                  # fetch one by id

xui.add_inbound({
    "remark": "my-inbound",
    "protocol": "vless",
    "port": 20000,
    "enable": True,
    "expiryTime": 0,
    "settings": {"clients": [], "decryption": "none"},
    "streamSettings": {"network": "tcp", "security": "none"},
    "sniffing": {"enabled": True, "destOverride": ["http", "tls", "quic", "fakedns"]},
})

xui.set_inbound_enable(1, False)    # disable
xui.reset_inbound_traffic(1)        # zero out traffic counters
xui.delete_inbound(1)               # remove
```

### Clients


**Fetch clients:**

```python
xui.get_clients()                    # every client, across all inbounds
xui.get_client("new-user")           # one client's full details
```

**Add a client:**

```python
xui.add_client(
    email="new-user",
    inbound_ids=None,          # attach to all current inbounds by default
    expiry_days=30,             # 0 = never expires
    total_gb=10,                 # 0 = unlimited
    limit_ip=2,                  # 0 = unlimited simultaneous IPs
)
```

**Update a client:**

```python
xui.update_client(
    "new-user",
    total_gb=20,
    expiry_days=60,
)
```

**Enable or disable a client:**

```python
xui.update_client("new-user", enable=False)
```

**Connection info:**

```python
xui.get_client_links("new-user")     # proxy links (vless://, vmess://, ...)
xui.get_client_traffic("new-user")   # up/down usage
xui.get_client_ips("new-user")       # connected source IPs
```

**Reset traffic:**

```python
xui.reset_client_traffic("new-user")
```

**Delete a client:**

```python
xui.delete_client("new-user")
xui.delete_client("new-user", keep_traffic=True)  # keep the traffic record
```

### Server

```python
xui.get_server_status()      # CPU, memory, disk, Xray state
xui.get_logs(count=50)       # last 50 lines of the panel log
```

### API tokens

```python
xui.get_api_tokens()                          # list every token
xui.create_api_token("my-bot-token")          # mint a new one — it's shown once
xui.set_api_token_enabled(token_id, False)    # disable without deleting
xui.delete_api_token(token_id)                # permanently revoke
```

More examples covering these and other flows are in [`examples/`](examples/).

## License

MIT