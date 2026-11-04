FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SAFE_STORAGE=/data SAFE_DB=/data/safe.db SAFE_ENV=production
WORKDIR /app
COPY requirements-web*.txt ./
RUN pip install --no-cache-dir -r requirements-web.txt && useradd --create-home safe && mkdir /data && chown safe:safe /data
COPY --chown=safe:safe . .
USER safe
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')"
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "180", "website:create_app()"]
