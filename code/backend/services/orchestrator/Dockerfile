FROM python:3.12-slim
WORKDIR /app
# Install verra-shared (local monorepo package) first
COPY packages/py_shared /tmp/py_shared
RUN pip install --no-cache-dir /tmp/py_shared
# Install service runtime deps
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" pydantic httpx
COPY services/orchestrator/app ./app
EXPOSE 8081
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
