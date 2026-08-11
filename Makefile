SHELL := /bin/sh

PYTHON ?= python3
VENV ?= .venv
PY ?= $(VENV)/bin/python
PIP = $(PY) -m pip
CONFIG ?= packages/configuration/config.txt

UNAME_S ?= $(shell uname -s)
ARCH ?= $(shell uname -m)

CORE_STAMP := $(VENV)/.core-installed
MLX_STAMP := $(VENV)/.mlx-installed
MLX_ARCHIVE := packages/mlx-2.2.tgz
MLX_BUILD_DIR := .build/mlx
MLX_WHEEL := $(MLX_BUILD_DIR)/ubuntu/mlx-2.2-py3-none-any.whl
MAZEGEN_SOURCES := $(wildcard packages/mazegen/src/mazegen/*.py)

MYPY_FLAGS := --warn-return-any --warn-unused-ignores \
	--ignore-missing-imports --disallow-untyped-defs \
	--check-untyped-defs

.PHONY: all install install-core install-mlx run debug clean lint \
	lint-strict test package help

all: install

$(PY):
	@$(PYTHON) -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)' \
		|| { printf '%s\n' 'Error: Python 3.10 or newer is required.' >&2; exit 1; }
	$(PYTHON) -m venv $(VENV)

$(CORE_STAMP): requirements.txt packages/mazegen/pyproject.toml \
	$(MAZEGEN_SOURCES) | $(PY)
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt
	$(PIP) install --no-build-isolation --force-reinstall packages/mazegen
	@touch $(CORE_STAMP)

install-core: $(CORE_STAMP)
	@printf '%s\n' '[Install] Python dependencies and mazegen are ready.'

$(MLX_WHEEL): $(MLX_ARCHIVE)
	@test "$(UNAME_S)" = "Linux" || { \
		printf '%s\n' 'Error: bundled MiniLibX targets Ubuntu Linux.' >&2; \
		exit 1; \
	}
	@test "$(ARCH)" = "x86_64" || { \
		printf '%s\n' 'Error: bundled MiniLibX requires x86_64.' >&2; \
		exit 1; \
	}
	mkdir -p $(MLX_BUILD_DIR)
	tar -xzf $(MLX_ARCHIVE) -C $(MLX_BUILD_DIR) \
		ubuntu/mlx-2.2-py3-none-any.whl

$(MLX_STAMP): $(MLX_WHEEL) | $(PY)
	$(PIP) install --no-deps --force-reinstall $(MLX_WHEEL)
	@$(PY) -c 'from mlx import Mlx; Mlx()' || { \
		printf '%s\n' \
			'Error: MiniLibX shared libraries are unavailable.' \
			'Ubuntu packages: libxcb1 libxcb-keysyms1 libvulkan1 zlib1g libbsd0' \
			>&2; \
		exit 1; \
	}
	@touch $(MLX_STAMP)

install-mlx: $(MLX_STAMP)
	@printf '%s\n' '[Install] Ubuntu MiniLibX is ready.'

install: install-core install-mlx
	@printf '%s\n' '[Install] A-Maze-ing installation complete.'

run: install
	$(PY) a_maze_ing.py $(CONFIG)

debug: install
	$(PY) -m pdb a_maze_ing.py $(CONFIG)

lint: install-core
	$(VENV)/bin/flake8 .
	$(VENV)/bin/mypy . $(MYPY_FLAGS)

lint-strict: install-core
	$(VENV)/bin/flake8 .
	$(VENV)/bin/mypy . --strict

test: install-core
	$(PY) -m pytest tests -q

package: install-core
	$(PY) -m build --wheel --no-isolation --outdir . packages/mazegen

clean:
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type d -name '*.egg-info' -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	rm -rf .build .mypy_cache .pytest_cache build dist
	rm -rf packages/mazegen/build packages/mazegen/dist
	@printf '%s\n' '[Clean] Caches and temporary build files removed.'

help:
	@printf '%s\n' \
		'make install       Create .venv and install mazegen + Ubuntu MLX' \
		'make install-mlx   Reinstall the bundled Ubuntu MLX wheel' \
		'make run           Generate and display using CONFIG=<path>' \
		'make debug         Run the configured maze under pdb' \
		'make lint          Run subject-required Flake8 and mypy checks' \
		'make lint-strict   Run Flake8 and mypy --strict' \
		'make test          Run the pytest suite' \
		'make package       Build mazegen wheel at repository root' \
		'make clean         Remove caches; preserve the submitted wheel'
