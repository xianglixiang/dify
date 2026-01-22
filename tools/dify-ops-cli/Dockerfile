FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app/

# Install dependencies (completed during build time in online environment)
RUN pip install --no-cache-dir -e .

# Set entrypoint
ENTRYPOINT ["dify-ops"]
CMD ["--help"]
