# 🕊️ Oldie-Goldie

*A Being Human Cult (BHC) Initiative*  

> **A self-hostable, peer-to-peer encrypted chat system**
> with tunnel-based connections and token-authenticated access.

[![PyPI Version](https://img.shields.io/pypi/v/oldie-goldie)](https://pypi.org/project/oldie-goldie/)
[![Python Versions](https://img.shields.io/pypi/pyversions/oldie-goldie)](https://pypi.org/project/oldie-goldie/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Issues](https://img.shields.io/github/issues/venukotamraju/Oldie-Goldie)](https://github.com/venukotamraju/Oldie-Goldie/issues)
[![Last Commit](https://img.shields.io/github/last-commit/venukotamraju/Oldie-Goldie)](https://github.com/venukotamraju/Oldie-Goldie/commits/main)

---

## 🌐 What is Oldie-Goldie?

**Oldie-Goldie** is an **on-demand**, **on-the-fly**, **self-hostable**, peer-to-peer encrypted chat system.
It provides **ephemeral tunnel-based connections** and **token-authenticated access**, enabling private, auditable, and serverless-style conversations between trusted peers.

---

## 💡 Why I Built It

### 🕵️ The Problem

Modern messaging services promise privacy — but often log metadata, store your messages, or use your data for ad targeting and behavioral profiling.
Even when encryption is claimed, the *closed-source* nature of these apps makes it impossible to know if your messages are truly private.

> “Mining for gold without opening the chest.”
> That’s how metadata surveillance works — who you message, when, how often — all reveal more than you think.

I wanted a fallback — a chat app that was:

* **Open source** and auditable
* **Truly self-hostable**
* **Peer-to-peer encrypted**, with **no middleman**

So I built **Oldie-Goldie**, and it became my trusted space for private discussions.

---

## 🧠 The Solution

Oldie-Goldie gives you:

* **Direct, secure, ephemeral connections**
* **No cloud storage**
* **No accounts**
* **End-to-end encrypted tunnels**
* **Invite-token based access control**

You spin up a temporary server, share a link + token with your peer, chat securely, and shut it all down when done.
Nothing is logged, nothing persists — just you and your peer.

---

## 🧭 Intended Usage

### Pre-requisite: Out-of-Band Sharing

1. **Usernames (pseudonyms)** — agree beforehand with your peer.
2. **PSK (pre-shared key)** — share a private key to authenticate tunnels.

### Flow for Global Server

0. Install the required **Cloudflared** package.
1. Start the server in tunneling mode (`--host public`) to get a temporary public URL.
2. Share that URL with your peer.
3. Both register using pseudonyms (not real names).
4. Use `/list_users` to find your peer.
5. Send a connection request via `/connect @username`.
6. Both enter the agreed **PSK** to authenticate the tunnel.
7. If PSK mismatches, the session is terminated, and usernames are blocked.

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

Generate tokens for two users:

```bash
og-server --host public --invite-token --bind alice bob
```

Then connect:

```bash
og-client --server-host public --url <server-url> --token <token>
```

---

## Cloudflared Installation on Ubuntu

1. Download the Debian Package via github.

```bash
 wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
```

2. Install the debian package

```bash
sudo dpkg -i cloudflared-linux-amd64.deb
```

## Cloudflared Installation on Windows

### Method-1

1. Download the .exe file from github (or) follow this url [cloudflared_exe_download](https://github.com/cloudflare/cloudflared/releases/download/2025.11.1/cloudflared-windows-amd64.exe).

2. Double click and install it and add the path in which cloudflared is installed to **Environment variables**.

### Method-2

1. Run the command prompt as **Administrator**.

2. execute the following command. So it will also add path to environment variables.

3. Make sure the PC is on latest version of either Windows 10/11.

```bash
winget install --id Cloudflare.cloudflared
```


## ⚙️ Installation

```bash
pip install oldie-goldie
```

---

## 🚀 Usage

### 🖥️ Run Server

#### Local

```bash
og-server --host local
```

#### Public (with Tunnel)

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

## 🧾 Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full version history and upcoming features.

---

## 🧪 Future Roadmap

* Extend safe_input with foreground/background input support
* Enable server-side dynamic token generation
* Add `--reuse` flag for token reuse
* Tidy server and client logs
* Improve modularity and developer docs
* Add Android support

---

## 🌿 About *Being Human Cult (BHC)*

The *Tech* wing of **Being Human Cult (BHC)** is a community-driven initiative focused on building humane, open-source technologies that empower people to connect authentically and privately — without exploitation, surveillance, or data harvesting.

Oldie-Goldie is developed and maintained under the BHC umbrella as a free and open-source project.  
Learn more: [https://beinghumancult.blogspot.com](https://beinghumancult.blogspot.com)

---

## ☕ Support the Project

Oldie-Goldie is free, open-source, and maintained with care by volunteers.
If you’d like to support development or buy the maintainers a coffee:

* 💖 **Buy Me a Coffee:** (link coming soon)
* 💰 **GitHub Sponsors:** (link coming soon)
* 🪙 **Ko-fi:** (link coming soon)
* 📢 **Share the project! —** word of mouth helps more than you think.

Your support keeps the project independent and privacy-focused. 🙏

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

Licensed under the [MIT License](LICENSE).  
Copyright © 2025  
**[Venu Kotamraju](https://github.com/venukotamraju)**, under the **Being Human Cult (BHC)** initative.

---

## 💬 Connect

* **GitHub** → [Oldie-Goldie](https://github.com/venukotamraju/Oldie-Goldie)
* **PyPI** → [oldie-goldie](https://pypi.org/project/oldie-goldie/)
* **LinkedIn** → *[Link coming soon...]*
* **Blog** → [Being Human Cult](https://beinghumancult.blogspot.com)

---

### 🧡 A Note from the Author

> I built Oldie-Goldie to reclaim digital privacy.
> It’s not about hiding — it’s about owning your data and choosing who gets to see it.

---

### ❤️ Author

**Venu Kotamraju**  
[kotamraju.venugopal@gmail.com](kotamraju.venugopal@gmail.com)  
[GitHub](https://github.com/venukotamraju)

---
