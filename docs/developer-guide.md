# 🔧 Developer Guide

> architecture, contribution, env setup

This guide explains the internal architecture, the development environment, and how to contribute safely and effectively to Oldie-Goldie.

---

## 🐍 Python Compatibility (Important)

Oldie-Goldie supports:

- **Python 3.10 – 3.13** ✔️  
- **Python 3.14** ❌ *Temporarily unsupported*

Python 3.14 is not yet supported because upstream dependencies (`cffi`, `cryptography`, etc.) have not released wheels for it.  
This leads to installation failures such as:

```bash
error: Failed to build 'cffi'
Microsoft Visual C++ 14.0 or greater is required
```

If your system Python is 3.14, you can still contribute using the methods below (no need to uninstall 3.14).

### Recommended environments

#### **Conda (easiest — Windows/macOS/Linux)**

```bash
conda create -n og-dev python=3.13
conda activate og-dev
```

#### **pyenv (Linux/macOS/WSL)**

```bash
pyenv install 3.13.1
pyenv local 3.13.1
```

#### **asdf (cross-platform)**

```bash
asdf install python 3.13.1
asdf local python 3.13.1
```

➡️ For detailed compatibility notes, see:  
[`python-compatibility.md`](python-compatibility.md)

---

## 📁 Repo Setup

```bash
git clone https://github.com/venukotamraju/Oldie-Goldie.git
cd Oldie-Goldie

python -m pip install -r requirements.txt
pip install -e .
```

### 🔬 Run Tests Locally

```bash
# No tests yet. (Coming soon.)
```

---

## 🏗 Architecture Overview

```markdown
Client ── handshake ──> Server ── establishes Cloudflared tunnel ──> Peer Client
                ↳ PSK validation
                ↳ token restrictions (optional)
```

### Key Principles

- The server **never stores messages** (no logs, no history)
- Tunnels are **ephemeral** and destroyed on disconnect
- All validation (token auth, PSK match, username checks) occurs **before** tunnel is established

The architecture is intentionally minimalistic for easier auditing and maximum privacy guarantees.

---

## 🤝 Contributing Workflow

1. **Fork** the repository  
2. Create a **feature branch**  
3. Write clean, descriptive commit messages  
4. Submit a **pull request** to `main`

Issues and feature proposals are welcome:  
<https://github.com/venukotamraju/Oldie-Goldie/issues>

---

## 📝 Notes for Developers

### Platform Markers Explained

Dependencies such as `cryptography` and `cffi` ship C/Rust extensions.  
To ensure Oldie-Goldie installs cleanly on all OSes and Python versions, platform markers are used:

```bash
cryptography>=42,<50 ; sys_platform != 'emscripten'
cffi>=1.15,<2        ; platform_machine != 'wasm32'
```

This prevents pip from attempting to install incompatible wheels in WebAssembly environments while keeping support stable on:

- Windows  
- Linux  
- macOS  

Python 3.10–3.13 currently supported.  
Python 3.14 support will be added once upstream wheels become available.

---

## 📚 Additional Docs

- **Compatibility Guide:** [`python-compatibility.md`](python-compatibility.md)
- **Usage Guide:** [`usage.md`](usage.md)
- **Project Overview & Landing Page:** [`index.md`](index.md)