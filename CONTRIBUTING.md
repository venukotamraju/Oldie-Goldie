# Contributing to Oldie-Goldie

Thank you for your interest in contributing! This guide will help you set up a development environment, understand the workflow, and safely contribute to the project.

---

## Maintainers

- **Venu Kotamraju** – Primary maintainer  
  Contact: <kotamraju.venugopal@gmail.com>  

For major changes or releases, please coordinate with the maintainer before pushing tags or publishing.

---

## Setup

1. **Clone the repository**

```bash
git clone https://github.com/venukotamraju/Oldie-Goldie.git
cd Oldie-Goldie
````

2. **Create a virtual environment**

```bash
python -m venv .ogdev
source .ogdev/bin/activate  # Linux/Mac
.ogdev\Scripts\activate     # Windows
```

3. **Install dependencies**

```bash
pip install --upgrade pip
pip install -e .
```

This will install the package in editable mode.

---

## Development Workflow

* **Run tests**

```bash
pytest tests/
```

* **Run server**

```bash
og-server --host local
```

* **Run client**

```bash
og-client --server-host local
```

* **Code style & formatting**

We follow PEP8. Use `black` for formatting:

```bash
pip install black
black .
```

---

## Versioning and Releases

We use [`bumpver`](https://github.com/ianheggie/bumpver) for semantic versioning.

**Typical workflow for a release:**

1. Make changes in your branch and merge into `main`.
2. Update `CHANGELOG.md` under "Unreleased".
3. Test locally.
4. Bump version:

```bash
bumpver minor   # or patch/major
```

5. Commit and push tag:

```bash
git push origin main --tags
```

6. CI/CD workflow will publish to PyPI/Test PyPI according to tag and versioning rules.

> **Note:** Only the maintainer should bump versions and trigger releases.

---

## GitHub Workflow

* Use feature branches for new features:
  `feature/<feature-name>`

* Use fix branches for bugs:
  `fix/<bug-name>`

* Pull requests must pass tests before merging.

---

## Reporting Issues

Please open issues in [GitHub Issues](https://github.com/venukotamraju/Oldie-Goldie/issues). Include:

* Steps to reproduce
* Expected behavior
* Actual behavior
* Logs if applicable

---

## Code of Conduct

Please follow [Contributor Covenant](https://www.contributor-covenant.org/) guidelines.

---
