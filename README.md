# 🕊️ Oldie-Goldie

*A Being Human Cult (BHC) Initiative*  

> **A self-hostable, peer-to-peer encrypted chat system  
with ephemeral tunnels, reusable invite tokens, and zero logs.**

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/oldie-goldie?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=MAGENTA&left_text=downloads)](https://pepy.tech/projects/oldie-goldie)

---

[![PyPI Version](https://img.shields.io/pypi/v/oldie-goldie)](https://pypi.org/project/oldie-goldie/)
![Cloudflared](https://img.shields.io/badge/cloudflared-auto--managed-ec5600)
![Security](https://img.shields.io/badge/encryption-end--to--end-green)
![Status](https://img.shields.io/badge/status-stable-blue)
[![Python Versions](https://img.shields.io/pypi/pyversions/oldie-goldie)](https://pypi.org/project/oldie-goldie/)
![Python 3.14](https://img.shields.io/badge/3.14-not%20yet%20supported-red)
[![License: Apache](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Issues](https://img.shields.io/github/issues/venukotamraju/Oldie-Goldie)](https://github.com/venukotamraju/Oldie-Goldie/issues)
[![Last Commit](https://img.shields.io/github/last-commit/venukotamraju/Oldie-Goldie)](https://github.com/venukotamraju/Oldie-Goldie/commits/main)

---

## 📘 Table of Contents

- [✨ Core Features](#-core-features)
- [⚡ TL;DR (Quick Start)](#-tldr-quick-start)
- [🌐 What is Oldie-Goldie?](#-what-is-oldie-goldie)
- [💡 Why I Built It](#-why-i-built-it)
- [🧭 Intended Usage](#-intended-usage)
- [🧱 Guard Rails and Trust Model](#-guard-rails-and-trust-model)
- [☁️ Cloudflared Handling (Automatic)](#️-cloudflared-handling-automatic)
- [⚙️ Installation](#️-installation)
- [🐍 Python Compatibility](#-python-compatibility)
- [🚀 Usage](#-usage)
- [📚 Documentation](#-documentation)
- [🧾 Changelog](#-changelog)
- [🧪 Future Roadmap](#-future-roadmap)
- [🌿 About Being Human Cult (BHC)](#-about-being-human-cult-bhc)
- [☕ Support the Project](#-support-the-project)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)
- [💬 Connect](#-connect)
- [🧡 A Note from the Author](#-a-note-from-the-author)
- [❤️ Author](#️-author)

---

## ✨ Core Features

- 🔐 **Encrypted peer-to-peer tunnels**
- 🪪 **Token-based access control** (single-use, bound, or reusable)
- 🔁 **Token reuse support (`--reuse`)**
- 🌐 **Automatic Cloudflared tunneling** (no installation required)
- 🧳 **Zero logs — nothing stored, nothing retained**
- 👥 **Ephemeral one-to-one private sessions**
- 🧩 **Cross-platform** (Linux · macOS · Windows)
- 🪶 **Lightweight Python CLI**
- 🕵️ **Privacy-first, open-source, auditable**

---

## ⚡ TL;DR (Quick Start)

**Start a public server (auto-tunnel + tokens):**

```bash
og-server --host public --invite-token --token-count 1 --reuse
```

**Client connects:**

```bash
og-client --server-host public --url <server-url> --token <token>
```

**Initiate a private encrypted tunnel:**

```bash
/connect @peer
```

**Enter your PSK → Tunnel established.**

---

## 🌐 What is Oldie-Goldie?

**Oldie-Goldie** is an **on-demand**, **peer-to-peer encrypted**, **self-hostable** chat system for people who want privacy without relying on centralized services.

You spin up a temporary server → share a URL + token → chat → destroy everything.  
Nothing persists. Nothing leaks.

---

## 💡 Why I Built It

### 🕵️ The Problem

Modern messaging services promise privacy — but often log metadata, store your messages, or use your data for ad targeting and behavioral profiling.
Even when encryption is claimed, the *closed-source* nature of these apps makes it impossible to know if your messages are truly private.

> “Mining for gold without opening the chest.”
> That’s how metadata surveillance works — who you message, when, how often — all reveal more than you think.

I wanted a fallback — a chat app that was:

- **Open source** and auditable
- **Truly self-hostable**
- **Peer-to-peer encrypted**, with **no middleman**

So I built **Oldie-Goldie**, and it became my trusted space for private discussions.

---

### 🧠 The Solution

Oldie-Goldie gives you:

- **Direct, secure, ephemeral connections**
- **No cloud storage**
- **No accounts**
- **End-to-end encrypted tunnels**
- **Invite-token based access control**

You spin up a temporary server, share a link + token with your peer, chat securely, and shut it all down when done.
Nothing is logged, nothing persists — just you and your peer.

---

## 🧭 Intended Usage

### Pre-requisite: Out-of-Band Sharing

1. **Usernames (pseudonyms)** — agree beforehand with your peer.
2. **PSK (pre-shared key)** — share a private key to authenticate tunnels.

### Flow for Global Server

> **Update (v0.6.0):**
> Oldie-Goldie now **automatically downloads and manages Cloudflared** using `pycloudflared`.  
> No installation. No PATH setup. Nothing manual.

1. Start the server (`--host public`)
2. Share the generated public URL
3. Register pseudonyms
4. `/list_users` to find your peer
5. `/connect @username`
6. Enter the shared **PSK**
7. The server relays traffic blindly over the encrypted tunnel

> ⚠️ **Disclaimer**
> Oldie-Goldie is **not** a social media or group chat platform.
> It’s designed for **private, ephemeral one-to-one communication**, where simplicity and trust are prioritized.

---

## 🧱 Guard Rails and Trust Model

| Layer                      | Purpose                     |
| -------------------------- | --------------------------- |
| Pre-shared pseudonyms      | Protects identity           |
| Pre-shared secret/password | Proof of identity           |
| Token-based access         | Prevents unauthorized entry |
| Temporary tunnels          | Ensure no data persistence  |

### 🔐 Example: Token-Based Secure Server

Generate bound tokens:

```bash
og-server --host public --invite-token --bind alice bob
```

Generate reusable tokens (v0.6.0):

```bash
og-server --host public --invite-token --bind alice bob --reuse
```

Then connect:

```bash
og-client --server-host public --url <server-url> --token <token>
```

---

## ☁️ Cloudflared Handling (Automatic)

Oldie-Goldie (v0.6.0) introduces **automatic integration** via `pycloudflared`.

### ✔ No manual installation needed  

### ✔ No PATH configuration  

### ✔ Works on Windows, Linux, macOS, and virtual environments  

### ✔ Cloudflared binary is downloaded automatically and sandboxed

This significantly simplifies public tunneling:

```bash
og-server --host public
```

Done. Tunneling works out of the box.

> Manual installation instructions are now unnecessary and removed.

---

## ⚙️ Installation

Oldie-Goldie supports *Python 3.10–3.13* on *Linux, macOS, and Windows*.

> **Note:** Python 3.14 is currently **not supported** due to missing upstream wheels (`cffi`, `cryptography`, etc.). See “[Python Compatibility](#-python-compatibility)” below.

### 📌 Standard Install

```bash
pip install oldie-goldie
```

#### 🧰 If pip is not recognized

```bash
python -m pip install oldie-goldie

# or

python3 -m pip install oldie-goldie
```

#### ✨ (Optional) Add pip to PATH

|OS|How|
|--|--|
|Windows|Add %LocalAppData%\Programs\Python\PythonXY\Scripts\ to PATH|
|Linux/macOS|Add ~/.local/bin to PATH|

#### ⬆️ Upgrade

```bash
pip install --upgrade oldie-goldie
```

### 🛠 Install from Source (for developers)

```bash
git clone https://github.com/venukotamraju/Oldie-Goldie.git
cd Oldie-Goldie
python -m pip install -r requirements.txt
pip install -e .
```

### 🧿 Troubleshooting

|Issue|Fix|
|-----|---|
|pip: comman not found|Use python -m pip or add pip to PATH|
|AttributeError: drain / asyncio mismatch|Upgrade Python to 3.10+ and reinstall|
|ModuleNotFoundError after install|Ensure you're using the same interpreter that installed the package|

---

## 🐍 Python Compatibility

### Supported Versions

✔ Python *3.10*  
✔ Python *3.11*  
✔ Python *3.12*  
✔ Python *3.13*

### Not Yet Supported

❌ **Python 3.14**  
→ Missing upstream wheels (`cryptography`, `cffi`)  
→ Support will be added automatically once dependencies publish them

Workarounds (pyenv, conda, etc.) included in [documentation](https://venukotamraju.github.io/Oldie-Goldie/python-compatibility/#workarounds-for-developers).

---

## 🚀 Usage

### 🖥️ Run Server

#### Local

```bash
og-server --host local
```

#### Public (with Automatic Tunnel)

```bash
og-server --host public
```

#### Protected (Invite Tokens)

```bash
og-server --host public --invite-token --token-count 2
```

#### Strongly Protected (Bound Tokens)

```bash
og-server --host public --invite-token --bind alice bob
```

#### Reusable Tokens (New in v0.6.0)

```bash
og-server --host public --invite-token --bind alice bob --reuse
```

---

### 💬 Run Client

#### Connect Locally

```bash
og-client --server-host local
```

#### Connect Remotely

```bash
og-client --server-host public --url <server-url>
```

#### Connect with Token

```bash
og-client --server-host public --url <server-url> --token <token>
```

---

## 📚 Documentation

Full usage guide · CLI examples · Architecture · Python compatibility · Changelog  
🔗 <https://venukotamraju.github.io/Oldie-Goldie>

---

## 🧾 Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full version history and upcoming features.

---

## 🧪 Future Roadmap

- Extend `safe_input` with foreground/background input support
- Enable server-side dynamic token generation
- Tidy client logs
- Add Android support
- Architectural docs expansion

---

## 🌿 About *Being Human Cult (BHC)*

The *Tech* wing of **Being Human Cult (BHC)** is a community-driven initiative focused on building humane, open-source technologies that empower people to connect authentically and privately — without exploitation, surveillance, or data harvesting.

Oldie-Goldie is developed and maintained under the BHC umbrella as a free and open-source project.  
Learn more: [https://beinghumancult.blogspot.com](https://beinghumancult.blogspot.com)

---

## ☕ Support the Project

Oldie-Goldie is free, open-source, and maintained with care by volunteers.
If you’d like to support development or buy the maintainers a coffee:

- 💖 **Buy Me a Coffee:** (link coming soon)
- 💰 **GitHub Sponsors:** (link coming soon)
- 🪙 **Ko-fi:** (link coming soon)
- 📢 **Share the project! —** word of mouth helps more than you think.

Your support keeps the project independent and privacy-focused. 🙏

---

## 🤝 Contributing

Pull requests are welcome!
If you’d like to contribute, please:

1. Fork the repo
2. Create a new branch
3. Make your changes
4. Submit a PR

Or open an [issue](https://github.com/venukotamraju/Oldie-Goldie/issues) to discuss ideas.

For more detailed developer setup and contributing guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📜 License

Licensed under the [APACHE 2.0](LICENSE).  
Copyright © 2025  
**[Venu Kotamraju](https://github.com/venukotamraju)**, under the **[Being Human Cult (BHC)](https://beinghumancult.blogspot.com)** initative.

---

## 💬 Connect

- **GitHub** → [Oldie-Goldie](https://github.com/venukotamraju/Oldie-Goldie)
- **PyPI** → [oldie-goldie](https://pypi.org/project/oldie-goldie/)
- **LinkedIn** → *[Link coming soon...]*
- **Blog** → [Being Human Cult](https://beinghumancult.blogspot.com)

---

## 🧡 A Note from the Author

> I built Oldie-Goldie to reclaim digital privacy.
> It’s not about hiding — it’s about owning your data and choosing who gets to see it.

---

## ❤️ Author

**Venu Kotamraju**  
[kotamraju.venugopal@gmail.com](kotamraju.venugopal@gmail.com)  
[GitHub](https://github.com/venukotamraju)

---
