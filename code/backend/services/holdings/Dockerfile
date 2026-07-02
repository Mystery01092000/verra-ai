FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" pydantic httpx pydantic-settings structlog prometheus-client
COPY packages/py_shared /opt/py_shared
RUN pip install --no-cache-dir /opt/py_shared
COPY services/holdings/app ./app
EXPOSE 8083
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8083"]
