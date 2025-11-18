# 💬 Usage Guide

> full CLI options + examples

This guide walks through running the Oldie-Goldie server and client, using tunnels, invite tokens, and peer-to-peer encrypted sessions.

---

## 🐍 Before You Begin

Oldie-Goldie supports **Python 3.10–3.13**.

If you're using Python 3.14, please read:  
📄 **[Python Compatibility Guide](python-compatibility.md)**

---

## 🖥️ Running the Server

Oldie-Goldie includes an interactive server that supports:

- Local mode  
- Public mode (via Cloudflared tunnel)  
- Invite-token mode  
- Bound-token mode  

---

### 🔒 Local Server

Runs the server on your machine with no tunnel.

```bash
og-server --host local
```

Useful for:

- Development  
- Offline usage  
- LAN-only communication  

---

### 🌍 Public Server (Cloudflared Tunnel)

Creates a temporary HTTPS-accessible public endpoint.

```bash
og-server --host public
```

The server will:

1. Launch a Cloudflared tunnel  
2. Generate a temporary public URL  
3. Display it for sharing  

Your peer can connect directly using that URL.

---

### 🔑 Invite-Protected Server

Limit access using auto-generated tokens.

```bash
og-server --host public --invite-token --token-count 2
```

- Tokens are single-use unless `--no-expiry` is used  
- Great for semi-trusted use cases  
- Prevents random users from joining your temporary public server  

---

### 🧍‍♂️🧍 Bound Token Mode (Strictest)

Use named, pre-bound tokens for two specific users.

```bash
og-server --host public --invite-token --bind alice bob
```

This mode ensures:

- Only *Alice* and *Bob* can join  
- Tokens cannot be borrowed or brute-forced  
- Only these two users can tunnel with each other  

---

## 💻 Running the Client

The client connects to a running server and provides a command-line chat UI with encrypted tunnel support.

---

### Local Connection

```bash
og-client --server-host local
```

---

### Remote Connection (Tunnel)

```bash
og-client --server-host public --url <server-url>
```

Example:

```bash
og-client --server-host public --url https://random-tunnel.trycloudflare.com
```

---

### Remote Connection with Token

```bash
og-client --server-host public --url <server-url> --token <token>
```

---

## 🔄 Typical Secure Conversation Flow

This is the recommended sequence for a private, ephemeral, peer-to-peer encrypted chat.

---

### 1️⃣ Start the Server

The host runs:

```bash
og-server --host public
```

or

```bash
og-server --host public --invite-token
```

---

### 2️⃣ Share the Connection Details

Send your peer:

- The URL  
- Optional token  
- Agreed **pseudonyms**  
- The **PSK (pre-shared key)**  

All of this must be shared out-of-band.

---

### 3️⃣ Register Using Pseudonyms

Each user enters a pseudonym when connecting.

Real names are discouraged.

---

### 4️⃣ Verify Presence

Use:

```bash
/list_users
```

to see who is connected.

---

### 5️⃣ Initiate a Connection Request

```bash
/connect @username
```

The peer will receive a request they can accept or deny.

---

### 6️⃣ Enter the PSK

Both sides will be prompted:

```bash
Enter pre-shared key:
```

- Input is hidden  
- Timeout protects against idle or malicious connections  
- Keys must match **exactly**  

---

### 7️⃣ Tunnel Opens

If both keys match:

- A secure, encrypted, isolated tunnel opens  
- Only the two participants may communicate inside it  

---

### 8️⃣ Mismatch Behavior

If the keys do **not** match:

- Tunnel is rejected  
- Both sides are disconnected  
- Usernames are temporarily blocked  

This prevents tunnel spamming and impersonation.

---

## 🧹 Commands Summary

| Command | Purpose |
|--------|---------|
| `/list_users` | Shows currently connected users |
| `/connect @user` | Initiates a secure tunnel request |
| `/accept` | Accepts a connection |
| `/deny` | Rejects a connection |
| `/exit_tunnel` | Leaves the active encrypted tunnel |
| `/help` | Shows help with colored output |

---

## ❗ Notes & Tips

- Tunnel messages are **not visible** to other connected users  
- Server logs never store chat content  
- Cloudflared tunnels close automatically when the server shuts down  
- If you get *input flickering*, ensure your terminal supports prompt_toolkit refresh  
- `/exit_tunnel` cleanly resets state on both sides  

---

## 📚 Related Documentation

- **Developer Guide** → [`developer-guide.md`](developer-guide.md)  
- **Compatibility Guide** → [`python-compatibility.md`](python-compatibility.md)
- **Project Overview** → [`index.md`](index.md)  
