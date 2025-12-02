# 🔧 Developer Guide  

Technical Internals · Architecture · Development Setup

This guide explains how Oldie-Goldie works internally, how to set up a development environment, and how to contribute safely and effectively.

---

## 🐍 Python Compatibility

Oldie-Goldie supports:

- ✔️ **Python 3.10 – 3.13**  
- ⚠️ **Python 3.14** — *temporarily unsupported* (missing upstream wheels for `cryptography`, `cffi`, etc.)

If your system Python is 3.14, you **do not** need to uninstall it.  
Use a dedicated environment:

---

### Recommended Development Environments

#### ▶ Conda (Windows/macOS/Linux — easiest)

```bash
conda create -n og-dev python=3.13
conda activate og-dev
```

#### ▶ pyenv (Linux/macOS/WSL)

```bash
pyenv install 3.13.1
pyenv local 3.13.1
```

#### ▶ asdf (cross-platform)

```bash
asdf install python 3.13.1
asdf local python 3.13.1
```

For detailed compatibility notes:  
📄 **[`python-compatibility.md`](python-compatibility.md)**

---

## 📁 Repository Setup

```bash
git clone https://github.com/venukotamraju/Oldie-Goldie.git
cd Oldie-Goldie

python -m pip install -r requirements.txt
pip install -e .
```

This installs the package in editable mode.

---

## 🧩 Project Architecture (High-Level)

Oldie-Goldie uses a **minimal, auditable, privacy-first** architecture.

```markdown
Client ── handshake ──> Server ── Cloudflared Tunnel ──> Peer Client
          ↳ token validation (optional)
          ↳ PSK authentication
          ↳ encrypted tunnel (peer-to-peer messaging)
```

### Key Behaviors

- **No message storage**  
  Server relays encrypted packets only; logs never contain message bodies.

- **Ephemeral tunnels**  
  Tunnel is created only when requested and torn down automatically on disconnect.

- **Modular client state machine**  
  States: `idle → request_sent / request_received → validating → tunnel_active`.

- **Decoupled encryption**  
  Encryption is performed client-side using a derived shared session key.

- **Token subsystem**  
  Supports single-use, reusable, bound, and non-expiring tokens.

---

## 🧱 Module Overview

A brief map of where core logic lives:

| Module | Purpose |
|--------|---------|
| `server/` | Server runtime, token validation, tunnel management |
| `client/` | Client runtime, input system, state machine |
| `shared/protocol/` | Message types, encryption/decryption flow |
| `shared/crypto/` | PSK → hashing → shared key → AES encryption |
| `client/helpers/` | Crypto helpers, key handling, client-side encryption utilities |
| `server/helpers` | Cloudflared integration & management |
| `utilities/` | Logging, async helpers, I/O wrappers |

This structure keeps privacy-critical code easy to audit.

---

## ▶ Running Locally in Dev Mode

### Start the server

```bash
python -m oldie_goldie.server.server --host local
```

### Start one or more clients

```bash
python -m oldie_goldie.client.chat --server-host local
```

Use `/list_users`, `/connect`, and `/exit_tunnel` to test tunnel flows.

---

## 🧪 Tests

Automated test suite coming soon.

Planned coverage:

- Token flows  
- PSK handshake timeout/mismatch  
- Encryption round-trip  
- State machine transitions  
- Cloudflared invocation logic  

---

## 🤝 Contributing

1. **Fork** the repo  
2. Create a **feature branch**  
3. Make your changes with clean commit messages  
4. Submit a **pull request** to `main`

Issues, ideas, and proposals are welcome:  
🔗 <https://github.com/venukotamraju/Oldie-Goldie/issues>

---

## 📝 Notes for Developers

### Why platform markers matter

Some dependencies include C/Rust extensions and must match your OS + Python version.  
Examples:

```text
cryptography>=42,<50 ; sys_platform != "emscripten"
cffi>=1.15,<2        ; platform_machine != "wasm32"
```

These prevent pip from installing incompatible wheels in unsupported environments (like WASM).

### Cloudflared Integration

Oldie-Goldie uses:

- **pycloudflared** for automatic download  
- seamless binary discovery per-environment  
- subprocess-based tunnel lifecycle

This eliminates manual installation for Windows/Linux/macOS.

---

## 📚 Related Documentation

- **Usage Guide** → [`usage.md`](usage.md)  
- **Compatibility Guide** → [`python-compatibility.md`](python-compatibility.md)  
- **Overview & Landing Page** → [`index.md`](index.md)  
