FROM python:3.12.7-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    libpq-dev \
    tzdata \
    && ln -fs /usr/share/zoneinfo/America/Bogota /etc/localtime \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
COPY . .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "os_simulator.wsgi:application", "--bind", "0.0.0.0:8000"]
