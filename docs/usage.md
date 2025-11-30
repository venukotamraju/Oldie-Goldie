# 💬 Usage Guide

This guide explains how to run the Oldie-Goldie **server** and **client**, use **invite tokens**, and establish **encrypted peer-to-peer tunnels**.

---

## 🐍 Before You Begin

Oldie-Goldie supports **Python 3.10–3.13**.

If you're on Python 3.14, read:  
📄 **[Python Compatibility](python-compatibility.md)**

---

## 🖥️ Running the Server

The server can run in:

- **Local mode** (no internet, LAN-only)  
- **Public mode** (Cloudflared tunnel)  
- **Invite-token mode** (access control)  
- **Bound-token mode** (strictest)  

---

### 🔒 Local Server

```bash
og-server --host local
```

Use for:

- LAN testing  
- Offline usage  
- Development  

No tunneling or tokens required.

---

### 🌍 Public Server (Cloudflared Tunnel)

Creates a temporary HTTPS URL using Cloudflared:

```bash
og-server --host public
```

The server will:

1. Auto-launch a Cloudflared tunnel  
2. Show a public URL  
3. Allow peers to connect using that URL  

Cloudflared is automatically managed via **pycloudflared**.

---

### 🔑 Invite-Protected Server

Restrict access using auto-generated one-time tokens:

```bash
og-server --host public --invite-token --token-count 2
```

Characteristics:

- Tokens expire after 10 minutes (default)
- By default, tokens are single-use
- Good for semi-trusted environments

---

### 🧍‍♂️🧍 Bound Tokens (Strictest Mode)

Bind tokens to specific usernames:

```bash
og-server --host public --invite-token --bind alice bob
```

Ensures:

- Only *Alice* and *Bob* can join
- Tokens cannot be used by others
- Only these two can tunnel with each other

---

## 💻 Running the Client

The client provides a real-time chat UI with encrypted tunnel support.

---

### Local Connection

```bash
og-client --server-host local
```

---

### Remote Connection

```bash
og-client --server-host public --url <server-url>
```

Example:

```bash
og-client --server-host public --url https://random-tunnel.trycloudflare.com
```

---

### Remote Connection (Token-Protected)

```bash
og-client --server-host public --url <server-url> --token <token>
```

---

## 🔄 Typical Secure Conversation Flow

A recommended sequence for private, ephemeral communication:

---

### 1️⃣ Start the Server

```bash
og-server --host public
```

or

```bash
og-server --host public --invite-token --token-count <int>
```

or

```bash
og-server --host public --invite-token --bind <pseudonym1> <pseudonym2> ...
```

---

### 2️⃣ Share the Required Details

Share out-of-band:

- Public URL  
- Invite token (if used)  
- Agreed **pseudonyms**  
- The **PSK (pre-shared key)**
    > *A **PSK** in this context/application is any string that only you two members, as a pair of tunnelers share/decide with each other and are aware of.*

---

### 3️⃣ Users Register via Pseudonyms

Real identities discouraged.

---

### 4️⃣ Verify Presence

```bash
/list_users
```

---

### 5️⃣ Initiate Tunnel Request

```bash
/connect @username
```

The peer receives a pop-up request.

---

### 6️⃣ Enter the PSK

Both are prompted:

```markdown
Enter pre-shared key:
```

- Input is hidden  
- PSK must match exactly  
- Timeout prevents hanging connections  

---

### 7️⃣ Tunnel Opens

If PSKs match:

- An encrypted, isolated tunnel opens  
- Only the two participants can communicate  
- Messages bypass global chat  

---

### 8️⃣ On PSK Mismatch

- Tunnel is rejected  
- Both clients disconnect  
- Usernames temporarily blocked  
- Prevents impersonation + tunnel spam

---

### 🧹 Commands Summary

| Command | Description |
|--------|-------------|
| `/list_users` | List connected users |
| `/connect @user` | Request a tunnel connection |
| `/accept` | Accept incoming tunnel request |
| `/deny` | Reject a tunnel request |
| `/exit_tunnel` | Leave active encrypted tunnel |
| `/help` | Show help with colored output |

---

## ❗ Notes & Tips

- A token has a default expiry time of **10 minutes**. To generate *no-expiry* tokens use `--no-expiry` flag  
- Username registration is time bound for **10 seconds**  
- PSK entry is time bound for **10seconds**  
- Tunnel messages are **not visible** to global users  
- Server does **not store** chat history  
- Cloudflared tunnel closes automatically with the server  
- If input flickers, ensure your terminal supports `prompt_toolkit`  
- `/exit_tunnel` resets state for both peers cleanly  

---

## 📚 Related Documentation

- **Developer Guide** → [`developer-guide.md`](developer-guide.md)  
- **Compatibility Guide** → [`python-compatibility.md`](python-compatibility.md)  
- **Project Overview** → [`index.md`](index.md)  
