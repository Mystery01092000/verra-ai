FROM python:3.12-slim
WORKDIR /app
# Install service runtime deps (incl. Bedrock + OpenAI SDKs)
RUN pip install --no-cache-dir \
    fastapi "uvicorn[standard]" pydantic httpx \
    "anthropic[bedrock]>=0.40" "openai>=1.30"
COPY services/model_gateway/app ./app
EXPOSE 8082
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8082"]
