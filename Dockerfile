# Wnesny (ونسني): optional Docker bonus (see README, section "Docker").
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WNESNY_ENV=development \
    DATABASE_URL=sqlite:////data/wnesny.db

WORKDIR /app

COPY requirements.txt requirements-analysis.txt ./
# Jupyter is left out of the image to keep it small (install it locally to run the notebook).
RUN grep -E '^[a-z]' requirements-analysis.txt | grep -v '^jupyter' | grep -v '^-r' > /tmp/analysis.txt \
    && pip install --no-cache-dir -r requirements.txt -r /tmp/analysis.txt

COPY . .
RUN chmod +x docker/entrypoint.sh \
    && useradd --create-home appuser \
    && mkdir -p /data /app/data/raw /app/instance \
    && chown -R appuser:appuser /data /app/data /app/instance
USER appuser

VOLUME ["/data"]
EXPOSE 5000

ENTRYPOINT ["docker/entrypoint.sh"]
CMD ["flask", "--app", "run.py", "run", "--host", "0.0.0.0", "--port", "5000"]
