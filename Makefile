# =========================================
# ANSI Escape Sequences
# =========================================
ESC         := \033
RESET       := $(ESC)[0m
GREEN       := $(ESC)[0;32m
YELLOW      := $(ESC)[0;33m
RED         := $(ESC)[0;31m
BLUE        := $(ESC)[0;34m
BOLD        := $(ESC)[1m
DIM         := $(ESC)[2m

# =========================================
# Variables
# =========================================
VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
CONFIG ?= config.txt
IMAGE := a-maze-ing-mlx

MYPY_FLAGS := --warn-return-any --warn-unused-ignores \
    --ignore-missing-imports --disallow-untyped-defs \
    --check-untyped-defs

.PHONY: install run debug clean lint lint-strict test package \
    docker-build docker-run shot help

# Install project dependencies and the mazegen package
install:
	@printf "$(GREEN)$(BOLD)[Install]$(RESET) $(GREEN)Installing dependencies...$(RESET)\n"
	$(PIP) install -r requirements.txt
	$(PIP) install -e packages/mazegen

# Run the main program
run:
	@printf "$(BLUE)$(BOLD)[Run]$(RESET) $(BLUE)Executing a_maze_ing.py...$(RESET)\n"
	$(PY) a_maze_ing.py $(CONFIG)

# Run the program in debug mode (pdb)
debug:
	@printf "$(YELLOW)$(BOLD)[Debug]$(RESET) $(YELLOW)Starting pdb...$(RESET)\n"
	$(PY) -m pdb a_maze_ing.py $(CONFIG)

# Remove temporary files, caches, and build artifacts
clean:
	@printf "$(RED)$(BOLD)[Clean]$(RESET) $(RED)Removing temporary files...$(RESET)\n"
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .mypy_cache .pytest_cache build dist shot.png
	rm -rf packages/mazegen/build packages/mazegen/dist
	find . -name '*.egg-info' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete 2>/dev/null || true

# Run linters (flake8 and mypy)
lint:
	@printf "$(BLUE)$(BOLD)[Lint]$(RESET) $(BLUE)Running flake8 and mypy...$(RESET)\n"
	$(VENV)/bin/flake8 .
	$(VENV)/bin/mypy . $(MYPY_FLAGS)

# Run strict linters
lint-strict:
	@printf "$(BLUE)$(BOLD)[Lint Strict]$(RESET) $(BLUE)Running strict linters...$(RESET)\n"
	$(VENV)/bin/flake8 .
	$(VENV)/bin/mypy . --strict

# Run tests using pytest
test:
	@printf "$(GREEN)$(BOLD)[Test]$(RESET) $(GREEN)Running pytest...$(RESET)\n"
	PYTHONPATH=. $(VENV)/bin/pytest tests -q

# Build the mazegen wheel package
package:
	@printf "$(YELLOW)$(BOLD)[Package]$(RESET) $(YELLOW)Building wheel...$(RESET)\n"
	$(PY) -m build --wheel --outdir . packages/mazegen

# Build the Docker image for Linux/MLX
docker-build:
	@printf "$(BLUE)$(BOLD)[Docker]$(RESET) $(BLUE)Building image $(IMAGE)...$(RESET)\n"
	docker build -t $(IMAGE) .

# Run the Docker container with VNC exposed
docker-run:
	@printf "$(GREEN)$(BOLD)[Docker]$(RESET) $(GREEN)Running container with VNC...$(RESET)\n"
	docker run --rm -it -e VNC=1 -p 5901:5900 -v "$(PWD)":/app $(IMAGE)

# Take a screenshot of the Xvfb screen inside Docker
shot:
	@printf "$(YELLOW)$(BOLD)[Shot]$(RESET) $(YELLOW)Taking screenshot...$(RESET)\n"
	docker run --rm -v "$(PWD)":/app $(IMAGE) bash -c \
	  'python3 a_maze_ing.py $(CONFIG) & sleep 4; \
	   import -window root /app/shot.png; kill %1 2>/dev/null || true'

# Display help information
help:
	@printf "$(BOLD)Available commands:$(RESET)\n"
	@printf "  $(GREEN)install$(RESET)      Install dependencies\n"
	@printf "  $(BLUE)run$(RESET)          Run the program\n"
	@printf "  $(YELLOW)debug$(RESET)        Run with pdb\n"
	@printf "  $(RED)clean$(RESET)        Remove temporary files and caches\n"
	@printf "  $(BLUE)lint$(RESET)         Run flake8 and mypy\n"
	@printf "  $(GREEN)test$(RESET)         Run pytest\n"
	@printf "  $(YELLOW)package$(RESET)      Build the mazegen wheel package\n"
	@printf "  $(BLUE)docker-build$(RESET) Build the Linux Docker image\n"
	@printf "  $(GREEN)docker-run$(RESET)   Run with VNC (vnc://localhost:5901, password: 1234)\n"
	@printf "  $(YELLOW)shot$(RESET)         Take a screenshot of the Xvfb screen as shot.png\n"