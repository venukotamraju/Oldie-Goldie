# Contributing to Oldie-Goldie

Thank you for your interest in contributing!  
This guide explains how to set up a development environment, follow the workflow, and contribute safely and effectively.

---

## 👥 Maintainers

- **Venu Kotamraju** – Primary maintainer  
  Contact: <kotamraju.venugopal@gmail.com>  

For major changes or releases, please coordinate with the maintainer before pushing tags or publishing.

---

## 🐍 Python Compatibility (Important)

Oldie-Goldie currently supports:

- **Python 3.10 – 3.13** ✔️  
- **Python 3.14** ❌ (not yet supported)

Python 3.14 is temporarily unsupported because upstream cryptographic dependencies (`cffi`, `cryptography`, etc.) do not yet publish wheels for it.

This may cause errors like:

```powershell
Microsoft Visual C++ 14.0 or greater is required
error: Failed to build 'cffi'
```

If you have Python 3.14 installed system-wide, no worries — you do **not** need to uninstall it.

### Recommended workarounds (choose one)

#### **A) Conda (Windows/macOS/Linux — easiest)**

```bash
conda create -n og-dev python=3.13
conda activate og-dev
```

#### **B) pyenv (Linux/macOS/WSL)**

```bash
pyenv install 3.13.1
pyenv local 3.13.1
```

#### **C) asdf (cross-platform)**

```bash
asdf install python 3.13.1
asdf local python 3.13.1
```

These ensure a stable environment without touching your system interpreter.

---

## 🛠️ Setup

1. **Clone the repository**

```bash
git clone https://github.com/venukotamraju/Oldie-Goldie.git
cd Oldie-Goldie
```

2. **Create a virtual environment (only if not using conda/pyenv/asdf)**

```bash
python -m venv .ogdev
source .ogdev/bin/activate     # Linux/Mac
.ogdev\Scripts\activate        # Windows
```

3. **Install dependencies**

```bash
pip install --upgrade pip
pip install -e .
pip install -r requirements.txt
```

This installs the package in editable development mode.

---

## 🧪 Development Workflow

### **Run tests**

```bash
pytest -vv
```

### **Run the server**

```bash
og-server --host local
```

### **Run the client**

```bash
og-client --server-host local
```

---

## 🧹 Code Style & Formatting

We follow:

- **PEP8**
- **Black** for formatting
- (Optional) `isort` for imports
- (Optional) `flake8` for linting

Format the repo:

```bash
pip install black
black .
```

---

## 🏷️ Versioning and Releases

We use **bumpver** for semantic versioning.

### Release workflow

1. Make changes in your feature branch
2. Update `CHANGELOG.md` under **Unreleased**
3. Ensure tests pass
4. Bump version:

```bash
bumpver patch    # or minor / major
```

5. Push the tag:

```bash
git push origin main --tags
```

> ⚠️ **Only the maintainer should bump versions and publish releases.**

---

## 🔀 Git Workflow

- New features → `feature/<name>`
- Bug fixes → `fix/<name>`
- All PRs must pass tests before merging.

---

## 🐛 Reporting Issues

Please open an issue with:

- Steps to reproduce  
- Expected vs actual behavior  
- Screenshots or logs  
- OS + Python version  
- Installation method (pip, venv, conda, pyenv)

Issues:  
<https://github.com/venukotamraju/Oldie-Goldie/issues>

---

## 🤝 Code of Conduct

This project follows the **Contributor Covenant**.  
Be respectful and constructive.

---

## ❤️ Thank You

Your contributions help keep this project secure, private, and open-source.  
We appreciate every PR, issue, suggestion, and improvement.
