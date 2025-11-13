# 🚀 Oldie Goldie — Release Workflow & Checklist

This guide describes how to version, tag, build, and publish *Oldie Goldie* to **Test PyPI** and **PyPI**, with GitHub Actions handling uploads automatically.

---

## 🧩 Prerequisites

- ✅ `pyproject.toml` fully configured (with entry points, metadata)
- ✅ GitHub repository linked and secrets added:
  - `TEST_PYPI_API_TOKEN`
  - `PYPI_API_TOKEN`
- ✅ GitHub Actions workflow `.github/workflows/publish.yml` set up

---

## 🧱 Local Build & Smoke Test (Optional, but Recommended)

Before publishing, test locally to confirm everything installs correctly.

```bash
rm -rf dist build *.egg-info
python -m build
pip install dist/oldie_goldie-<version>-py3-none-any.whl --force-reinstall
og-server --help
og-client --help
````

---

## 🧮 Version Management with bumpver

Add this file as `.bumpver.toml` in your repo:

```toml
[bumpver]
current_version = "0.5.0b1"
version_pattern = "MAJOR.MINOR.PATCH[PYTAGNUM]"
commit_message = "🔖 bump version to {new_version}"
tag_message = "Release {new_version}"
tag_scope = "repository"
push = true

[bumpver.file_patterns]
"pyproject.toml" = ['version = "{version}"']
"CHANGELOG.md" = ["## \\[{version}\\]"]
```

---

### 🔁 Bumping Versions

| Action         | Command                              | Example        |
| -------------- | ------------------------------------ | -------------- |
| Bump patch     | `bumpver update --patch`             | → 0.5.1b1      |
| Bump minor     | `bumpver update --minor`             | → 0.6.0b1      |
| Bump to stable | `bumpver update --set-version 0.5.0` | drops beta tag |

> 💡 bumpver automatically commits, tags, and pushes if configured with `push = true`.

---

## 🧾 Release Checklist

### ✅ 1. Finalize Changelog

In `CHANGELOG.md`, rename **Unreleased** → `[vX.Y.Z] - YYYY-MM-DD` and ensure entries are accurate.

```bash
git add CHANGELOG.md
git commit -m "📝 Update changelog for vX.Y.Z"
```

---

### ✅ 2. Bump Version & Tag

For **beta/pre-release:**

```bash
bumpver update --set-version 0.5.0b1
```

For **stable release:**

```bash
bumpver update --set-version 0.5.0
```

This will:

- Update version in `pyproject.toml`
- Commit & tag the release (e.g., `v0.5.0b1`)
- Push the tag → which triggers GitHub Action to upload to TestPyPI / PyPI automatically

---

### ✅ 3. Verify Build Artifacts

After the workflow runs, check the run logs under
→ **GitHub → Actions → Publish Python 🐍 Package**

Or manually:

```bash
twine check dist/*
```

---

### ✅ 4. Verify on PyPI/TestPyPI

#### For TestPyPI

```bash
pip install -i https://test.pypi.org/simple/ oldie-goldie
```

#### For Production

```bash
pip install oldie-goldie
```

---

### ✅ 5. Post-Release Updates

- Commit any final doc updates
- Announce on GitHub Releases, add screenshots, and update README if needed
- Optionally post your release demo / announcement on LinkedIn 🎉

---

### ✅ 6. Next Development Cycle

After a stable release:

```bash
bumpver update --patch --tag beta
```

This bumps you to `0.5.1b1` — next development cycle begins cleanly.

---

## 🧰 (Optional) — Makefile for Automation

For faster workflow, add a simple `Makefile`:

```makefile
build:
 python -m build

test-install:
 pip install dist/*.whl --force-reinstall

clean:
 rm -rf dist build *.egg-info

release-beta:
 bumpver update --set-version $(VERSION)b1

release-stable:
 bumpver update --set-version $(VERSION)
```

Then you can run:

```bash
make build
make release-beta VERSION=0.6.0
```

---

### 🌈 Summary

| Stage         | Command                                                     | Output         |
| ------------- | ----------------------------------------------------------- | -------------- |
| Build locally | `python -m build`                                           | wheel & tar.gz |
| Test locally  | `pip install dist/*.whl`                                    | installs app   |
| Tag & push    | `bumpver update --set-version 0.6.0b1`                      | auto upload    |
| Verify        | `pip install -i https://test.pypi.org/simple/ oldie-goldie` | ✅              |
| Release       | `bumpver update --set-version 0.6.0`                        | 🏁 stable      |

---

## ✅ What Happens After You Add This

1. You **run one command**:  

   ```bash
   bumpver update --set-version 0.5.0b1
    ```

2. It updates your version, commits, and pushes a tag.
3. GitHub Actions sees the tag, builds, and uploads to **TestPyPI**.
4. You test it with

   ```bash
   pip install -i https://test.pypi.org/simple/ oldie-goldie
   ```

5. When ready, bump again to stable

   ```bash
   bumpver update --set-version 0.5.0
   ```

6. GitHub Actions uploads to **real PyPI** automatically.

---
