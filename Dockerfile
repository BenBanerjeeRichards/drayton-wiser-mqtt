# --- Stage 1: Build Frontend ---
FROM node:22-slim AS fe-builder
WORKDIR /build-fe
COPY thermostat-fe/package*.json ./
RUN npm install
COPY thermostat-fe/ ./
RUN npm run build

# --- Stage 2: Build Backend ---
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# 1. Explicitly copy project files so they persist for subsequent RUN commands
COPY pyproject.toml uv.lock ./

# 2. Install dependencies (cached layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# 3. Copy your Python source code
COPY src/ /app/src/

# 4. Final sync to install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked


# --- Stage 3: Final Runtime ---
FROM python:3.14-slim-bookworm

RUN groupadd --system --gid 999 nonroot \
 && useradd --system --gid 999 --uid 999 --create-home nonroot

WORKDIR /app

# Copy the virtual environment and the source code
COPY --from=builder --chown=nonroot:nonroot /app /app

# Copy the React static build
COPY --from=fe-builder --chown=nonroot:nonroot /build-fe/dist /app/dist

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
USER nonroot

# Note: Ensure main.py is inside the src/ directory
CMD ["python", "src/main.py"]