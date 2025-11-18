# 🐍 Python Compatibility Matrix

Oldie-Goldie depends on low-level cryptographic libraries that require
pre-built Python wheels for smooth installation on all platforms.

Because Python 3.14 introduces ABI/runtime changes, several dependencies have not yet released wheels for it.

---

## ✅ Supported Python Versions

| Python Version | Supported | Notes |
|----------------|-----------|-------|
| 3.10 | ✔️ | Fully supported |
| 3.11 | ✔️ | Fully supported |
| 3.12 | ✔️ | Fully supported |
| 3.13 | ✔️ | Fully supported |
| 3.14 | ❌ | Pending upstream support |

---

## 🧱 Why Python 3.14 is Not Supported Yet

The following packages currently lack Python 3.14 wheels:

- *cffi*
- *cryptography*
- *websockets*
- indirect crypto dependencies

These packages require C extensions, so compilation fails on many systems (especially Windows) unless a full compiler toolchain is installed.

Once PyPI publishes stable 3.14 wheels, Oldie-Goldie will lift the restriction.

---

## 🔧 Workarounds (No Need to Uninstall Python 3.14)

You can keep 3.14 as your system Python and run Oldie-Goldie using:

### Option A — Conda (Recommended)

```bash
conda create -n og-env python=3.13
conda activate og-env
```

### Option B — pyenv

```bash
pyenv install 3.13.1
pyenv local 3.13.1
```

### Option C — asdf version manager

```bash
asdf install python 3.13.1
asdf local python 3.13.1
```

These solutions isolate the environment without affecting your system Python.

---

## 📅 Roadmap for Python 3.14 Support

Oldie-Goldie will add official support when:

1. cryptography publishes wheels for Python 3.14  
2. cffi publishes wheels for Python 3.14  
3. websockets publishes wheels for Python 3.14  
4. Windows/macOS/Linux wheels are all available  
5. Full installation + runtime tests pass  

Progress is tracked in:  
🔗 <https://github.com/venukotamraju/Oldie-Goldie/issues>

---

If you encounter compatibility issues, please open an issue with:

- OS
- Python version
- pip version
- full error log

Thanks for helping make Oldie-Goldie better! ❤️
