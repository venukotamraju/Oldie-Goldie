# 🐍 Python Compatibility Guide

Oldie-Goldie supports modern Python versions on Windows, macOS, and Linux.  
Because the project relies on cryptographic packages with native components, compatibility depends on upstream wheel availability.

---

## ✔️ Supported Python Versions

| Python Version | Status | Notes |
|----------------|--------|-------|
| **3.10** | ✅ Supported | Fully tested |
| **3.11** | ✅ Supported | Stable |
| **3.12** | ✅ Supported | Stable |
| **3.13** | ✅ Supported | Stable |
| **3.14** | ❌ Not supported | Missing upstream wheels |

---

## ❗ Why Python 3.14 Is Not Supported Yet

Python 3.14 introduces ABI/runtime changes that require C-extension packages to release updated wheels.  
As of now, these libraries **do not ship 3.14 wheels**:

- `cryptography`  
- `cffi`  
- Their transitive dependencies  

Because of this, pip tries to **compile from source**, typically resulting in errors like:

```powershell
Microsoft Visual C++ 14.0 or greater is required
error: Failed to build 'cffi'
```

Once wheels are published for all platforms, Oldie-Goldie will automatically enable 3.14 support.

Track progress:  
🔗 <https://github.com/venukotamraju/Oldie-Goldie/issues>

---

## 🧪 Workarounds for Developers

You do **not** need to uninstall Python 3.14.  
Create an isolated environment with a supported version:

---

### 🟩 Option 1 — Conda (Recommended for Windows)

```bash
conda create -n og-dev python=3.13
conda activate og-dev
```

Zero compiler requirements.

---

### 🟦 Option 2 — pyenv (Linux/macOS/WSL)

```bash
pyenv install 3.13.1
pyenv local 3.13.1
```

Keeps system Python untouched.

---

### 🟪 Option 3 — asdf (Cross-platform)

```bash
asdf install python 3.13.1
asdf local python 3.13.1
```

Ideal for multi-language setup consistency.

---

## 🔮 Roadmap for 3.14 Support

Oldie-Goldie will adopt Python 3.14 once the ecosystem provides:

1. Official 3.14 wheels for `cffi`  
2. Updated `cryptography` wheels depending on that release  
3. Complete wheel coverage across Windows, Linux, macOS  
4. Installation that requires **no compilers**  

Until then, 3.14 is intentionally disabled to avoid build errors and confusing installation failures.

---

## 📚 Related Documentation

- **Developer Guide:** [`developer-guide.md`](developer-guide.md)  
- **Usage Guide:** [`usage.md`](usage.md)  
- **Overview:** [`index.md`](index.md)  
