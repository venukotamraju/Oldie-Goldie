# ===============================
#   Oldie-Goldie Makefile
# ===============================

# 🧱 Variables
PACKAGE = oldie-goldie
PYTHON = python3

# Default target
help:
	@echo ""
	@echo "Oldie-Goldie Developer Commands"
	@echo "--------------------------------"
	@echo "make build        - Build the package (wheel + sdist)"
	@echo "make clean        - Remove build and dist artifacts"
	@echo "make install      - Install the package locally"
	@echo "make testpypi     - Upload build to TestPyPI"
	@echo "make publish      - Upload build to PyPI"
	@echo "make docs         - Build and serve docs locally"
	@echo "make bump-beta    - Bump pre-release version (beta)"
	@echo "make push         - Push main + tags to remote"
	@echo ""

# 🧹 Cleanup
clean:
	rm -rf build dist *.egg-info
	find . -name "__pycache__" -type d -exec rm -rf {} +

# ⚙️ Build package
build: clean
	$(PYTHON) -m build

# ✅ Validate metadata
check:
	twine check dist/*

# 🧩 Local install
install: build
	pip install --force-reinstall dist/*.whl

# 🧪 Publish to TestPyPI
testpypi: build check
	twine upload --repository testpypi dist/*

# 🚀 Publish to PyPI
publish: build check
	twine upload dist/*

# 🔖 Version bump targets
bump-patch:
	bumpver update --patch

bump-minor:
	bumpver update --minor

bump-major:
	bumpver update --major

bump-beta:
	bumpver update --tag=beta

# 📤 Push to GitHub (main + tags)
push:
	git push origin main --tags

# 📚 Build and serve docs locally
docs:
	mkdocs serve

.PHONY: help clean build check install testpypi publish docs \
        bump-patch bump-minor bump-major bump-beta push
