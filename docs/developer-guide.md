# 🔧 Developer Guide

> architecture, contribution, env setup

## Repo Setup

```bash
git clone https://github.com/venukotamraju/Oldie-Goldie.git
cd Oldie-Goldie
python -m pip install -r requirements.txt
pip install -e .
```

### Run tests locally

```bash
# No Tests Yet. Will Update in future.
```

---

## Architecture Overview (high level)

```markdown
Client ── handshake ──> Server ── establishes Cloudflared tunnel ──> Peer Client  
                ↳ PSK validation  
                ↳ token restrictions (optional)
```

- Server **never stores messages**

- Tunnels are **ephemeral** and exist only for the session

- All validation happens **before tunnel establishment**

---

## Contributing

1. Fork the repository

2. Create a feature branch

3. Write clear commit messages

4. Submit a pull request

Issues & feature proposals welcome:
<https://github.com/venukotamraju/Oldie-Goldie/issues>

## Notes

### Platform Markers Explained

> You can observe these in pyproject.toml

Some dependencies (like cryptography and cffi) include native C/Rust extensions.
To ensure Oldie-Goldie installs cleanly on all platforms, we use platform markers,
so pip resolves the correct wheel per OS and Python version:

Example:

cryptography>=42,<50 ; sys_platform != 'emscripten'
cffi>=1.15,<2        ; platform_machine != 'wasm32'

This avoids installation failures on experimental environments such as WebAssembly
while remaining fully compatible with Windows / Linux / macOS on Python 3.10–3.14.
