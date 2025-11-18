# 🐍 Python Compatibility Guide

Oldie-Goldie aims to support modern Python versions across Windows, macOS, and Linux.  
Because the project uses cryptographic dependencies with native components, compatibility depends on upstream wheels.

---

## ✔️ Supported Python Versions

| Python Version | Status | Notes |
|----------------|--------|-------|
| **3.10** | ✅ Supported | Fully tested |
| **3.11** | ✅ Supported | Stable |
| **3.12** | ✅ Supported | Stable |
| **3.13** | ✅ Supported | Stable |
| **3.14** | ❌ Not yet supported | Pending upstream wheels |

---

## ❗ Why Python 3.14 Is Not Supported Yet

Python 3.14 introduces ABI/runtime changes that require C extension packages to publish updated wheels.  
These packages currently do **not** provide 3.14 wheels:

- `cffi`
- `cryptography`
- Transitive dependencies

As a result, pip attempts to **compile from source**, triggering failures like:

```powershell
Microsoft Visual C++ 14.0 or greater is required
error: Failed to build 'cffi'
```

Once upstream wheels land on PyPI, Oldie-Goldie will enable 3.14 support automatically.

Track progress here:  
<https://github.com/venukotamraju/Oldie-Goldie/issues>

---

## 🧪 Workarounds for Contributors

You do **not** need to uninstall Python 3.14.  
Choose one of the following recommended approaches:

---

### 🟩 Option 1 — Conda Environment (Recommended for Windows)

```bash
conda create -n og-dev python=3.13
conda activate og-dev
```

Works out-of-the-box with zero compiler requirements.

---

### 🟦 Option 2 — pyenv (Linux/macOS/WSL)

```bash
pyenv install 3.13.1
pyenv local 3.13.1
```

Keeps system Python untouched.

---

### 🟪 Option 3 — asdf (Cross-Platform)

```bash
asdf install python 3.13.1
asdf local python 3.13.1
```

Very reliable for multi-language setups.

---

## 🔮 Roadmap for 3.14 Support

Oldie-Goldie will adopt Python 3.14 once:

1. `cffi` publishes official wheels  
2. `cryptography` updates to depend on them  
3. Wheels exist for Windows, macOS, and Linux  
4. Installation succeeds without compilers  

Until then, 3.14 remains unsupported for stability and developer experience.

---

## 📚 See Also

- **Developer Guide:** [`developer-guide.md`](developer-guide.md)  
- **Contributing Guide:** [`CONTRIBUTING.md`](../CONTRIBUTING.md)  
- **Project Homepage:** [`index.md`](index.md)  
