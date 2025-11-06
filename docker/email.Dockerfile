# Email Connector Service Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Python dependencies
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    requests==2.31.0 \
    beautifulsoup4==4.12.2 \
    lxml==4.9.3 \
    httpx==0.25.1 \
    email-validator==2.1.0

# Copy connector code
COPY src/connectors/email/ /app/email_connector/

# Copy shared utils (optional, si nécessaire)
# COPY src/connectors/base.py /app/

EXPOSE 5008

CMD ["uvicorn", "email_connector.server:app", "--host", "0.0.0.0", "--port", "5008"]
