FROM python:3.9-slim

# Install required system packages
RUN apt-get update && apt-get install -y \
    python3-dev \
    libudev-dev \
    gcc \
    kmod \
    && rm -rf /var/lib/apt/lists/*

# copy requirements.txt
COPY requirements.txt /tmp/requirements.txt

# Install python packages
RUN pip install -r /tmp/requirements.txt

# Copy the virtual touch script
COPY virtual_touch.py /app/virtual_touch.py

WORKDIR /app

CMD ["python", "/app/virtual_touch.py"]