FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python scripts/generate_assets.py
EXPOSE 8000 8501
CMD ["sh", "-c", "python -m backend.bootstrap && uvicorn backend.main:app --host 0.0.0.0 --port 8000 & streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501 --server.enableCORS false --server.enableXsrfProtection false"]
