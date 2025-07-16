FROM public.ecr.aws/lambda/python:3.12

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set up environment variables for uv
ENV \
    UV_CACHE_DIR=/tmp/.cache \
    UV_PYTHON_DOWNLOADS=never \
    UV_LOCKED=1 \
    UV_PROJECT_ENVIRONMENT=${LAMBDA_TASK_ROOT}/.venv

# Copy project files
COPY pyproject.toml uv.lock ${LAMBDA_TASK_ROOT}/
COPY source/ ${LAMBDA_TASK_ROOT}/source/
COPY services/lambda/bda-report-processor/ ${LAMBDA_TASK_ROOT}/

RUN cd ${LAMBDA_TASK_ROOT} && \
    uv venv .venv && \
    uv sync --no-dev --no-editable

ENV PYTHONPATH="${LAMBDA_TASK_ROOT}/.venv/lib/python3.12/site-packages:${LAMBDA_TASK_ROOT}/source:${PYTHONPATH}"

CMD ["main.handler"]

