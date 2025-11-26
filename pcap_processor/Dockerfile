FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (libpcap is needed for cicflowmeter)
RUN apt-get update && apt-get install -y \
    libpcap-dev tcpdump \
    && rm -rf /var/lib/apt/lists/*

# Install cicflowmeter
# Note: Using a specific version or a fork might be necessary if the original is unmaintained,
# but for now we'll try the standard package.
RUN pip install cicflowmeter pandas requests

COPY process.py .

CMD ["python", "process.py"]
