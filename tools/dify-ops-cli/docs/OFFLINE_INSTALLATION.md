# Offline Installation Guide

This guide explains how to deploy and use dify-ops-cli in completely offline or air-gapped enterprise environments.

## Overview

dify-ops-cli is designed to work in offline environments with the following characteristics:

✅ **Fully Offline Runtime**: Only requires access to your local Dify API
✅ **No External Dependencies**: No telemetry, analytics, or cloud service calls
✅ **Flexible SSL**: Supports self-signed certificates or disabled SSL verification
✅ **Local Configuration**: All settings via YAML files and environment variables

⚠️ **One-Time Setup**: Initial installation requires downloading dependencies (31 packages) in an online environment, then transferring to offline environment.

## Deployment Options

Choose the deployment method that best fits your environment:

1. **[Docker Image](#option-1-docker-offline-image)** (Recommended) - Self-contained, easy to deploy
2. **[Wheel Package](#option-2-offline-wheel-package)** - Traditional Python package installation

## Option 1: Docker Offline Image

### Prerequisites

- Docker installed in both online and offline environments
- Linux x86_64 architecture (or build for your platform)

### Step 1: Build Image (Online Environment)

```bash
# Navigate to project directory
cd tools/dify-ops-cli

# Build and export Docker image
./scripts/build-docker-offline.sh
```

This creates: `dist/dify-ops-cli-v0.1.0.tar.gz` (approximately 150-200MB)

### Step 2: Transfer to Offline Environment

Transfer the image file to your offline environment using your organization's approved method (USB drive, secure file transfer, etc.):

```bash
# Example: Using scp through a secure gateway
scp dist/dify-ops-cli-v0.1.0.tar.gz user@offline-host:/tmp/
```

### Step 3: Load Image (Offline Environment)

```bash
# Load Docker image
docker load -i dify-ops-cli-v0.1.0.tar.gz

# Verify image loaded
docker images | grep dify-ops-cli
# Should show: dify-ops-cli   v0.1.0   ...
```

### Step 4: Run Commands

```bash
# Show help
docker run dify-ops-cli:v0.1.0

# Validate configuration file
docker run -v $(pwd):/config dify-ops-cli:v0.1.0 \
  config validate /config/config.yaml

# Apply configuration (with environment variables)
docker run \
  -v $(pwd):/config \
  -e DIFY_API_KEY=$DIFY_API_KEY \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  dify-ops-cli:v0.1.0 \
  apply /config/config.yaml
```

### Docker Best Practices

**Create a shell alias for convenience:**

```bash
# Add to ~/.bashrc or ~/.zshrc
alias dify-ops='docker run -v $(pwd):/config -e DIFY_API_KEY -e OPENAI_API_KEY dify-ops-cli:v0.1.0'

# Then use normally:
dify-ops config validate config.yaml
dify-ops apply config.yaml
```

**For production deployments:**

```bash
# Use environment file
docker run \
  -v $(pwd):/config \
  --env-file /path/to/production.env \
  dify-ops-cli:v0.1.0 \
  apply /config/config.yaml
```

## Option 2: Offline Wheel Package

### Prerequisites

- Python 3.11+ installed in offline environment
- Linux x86_64 architecture

### Step 1: Build Package (Online Environment)

```bash
# Navigate to project directory
cd tools/dify-ops-cli

# Generate requirements file (if not exists)
source .venv/bin/activate
uv pip freeze | grep -v '^-e' > requirements.txt

# Build offline package
./scripts/build-offline-package.sh
```

This creates: `dist/dify-ops-cli-offline-v0.1.0.tar.gz` (approximately 20-30MB)

### Step 2: Transfer to Offline Environment

Transfer the package file to your offline environment:

```bash
# Example transfer
scp dist/dify-ops-cli-offline-v0.1.0.tar.gz user@offline-host:/tmp/
```

### Step 3: Install (Offline Environment)

```bash
# Extract package
tar -xzf dify-ops-cli-offline-v0.1.0.tar.gz
cd wheels  # Or extracted directory name

# Run installation script
./install-offline.sh
```

The script will:
1. Create a Python virtual environment
2. Install all dependencies from wheel files
3. Install dify-ops-cli
4. Verify the installation

### Step 4: Use the Tool

```bash
# Activate virtual environment
source .venv/bin/activate

# Verify installation
dify-ops --version

# Use commands
dify-ops config validate config.yaml
dify-ops apply config.yaml

# Deactivate when done
deactivate
```

## Configuration for Offline Environments

### Disabling SSL Verification

If your internal Dify API uses self-signed certificates:

```yaml
# config.yaml
version: "1.0"

connection:
  api_url: "https://dify.internal.company.com"
  api_key: "${DIFY_API_KEY}"
  verify_ssl: false  # Disable SSL verification
```

### Using Custom CA Certificates

For enterprise CA certificates, set the environment variable:

```bash
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/company-ca-bundle.crt
export SSL_CERT_FILE=/etc/ssl/certs/company-ca-bundle.crt
```

Or in Docker:

```bash
docker run \
  -v /etc/ssl/certs:/etc/ssl/certs:ro \
  -e SSL_CERT_FILE=/etc/ssl/certs/company-ca-bundle.crt \
  -v $(pwd):/config \
  dify-ops-cli:v0.1.0 \
  apply /config/config.yaml
```

## Example: Complete Offline Setup

### 1. Create Configuration File

```yaml
# offline-config.yaml
version: "1.0"

metadata:
  name: "Offline Enterprise Setup"
  description: "Configuration for air-gapped environment"

connection:
  api_url: "https://dify.internal.company.com"
  api_key: "${DIFY_API_KEY}"
  verify_ssl: false  # Using self-signed cert

tenants:
  - name: "Production Workspace"
    email: "admin@company.com"
    language: "en-US"

    model_providers:
      - provider: "openai"
        credentials:
          openai_api_key: "${OPENAI_API_KEY}"
        models:
          - model: "gpt-4o"
            model_type: "llm"
            enabled: true

options:
  idempotent: true
  fail_fast: false
```

### 2. Set Environment Variables

```bash
# Create .env file
cat > .env <<EOF
DIFY_API_KEY=your-dify-api-key
OPENAI_API_KEY=sk-your-openai-key
EOF

# Load environment
export $(cat .env | xargs)
```

### 3. Preview and Apply

```bash
# Preview changes (dry-run)
dify-ops apply offline-config.yaml --dry-run

# Apply configuration
dify-ops apply offline-config.yaml

# With Docker:
docker run -v $(pwd):/config --env-file .env \
  dify-ops-cli:v0.1.0 apply /config/offline-config.yaml
```

## Troubleshooting

### Issue: SSL Certificate Verification Failed

**Symptoms:**
```
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**Solution:**
1. Set `verify_ssl: false` in configuration
2. Or provide valid CA certificate via `SSL_CERT_FILE`

### Issue: Command Not Found After Installation

**Symptoms:**
```bash
$ dify-ops --version
bash: dify-ops: command not found
```

**Solution:**
```bash
# Activate virtual environment
source .venv/bin/activate

# Or use full path
.venv/bin/dify-ops --version
```

### Issue: Docker Container Cannot Access Host Network

**Symptoms:**
```
Failed to connect to https://dify.internal.company.com
```

**Solution:**
```bash
# Use host network mode
docker run --network=host \
  -v $(pwd):/config \
  dify-ops-cli:v0.1.0 \
  apply /config/config.yaml

# Or specify internal DNS
docker run --dns=10.0.0.1 \
  -v $(pwd):/config \
  dify-ops-cli:v0.1.0 \
  apply /config/config.yaml
```

### Issue: Permission Denied on Scripts

**Symptoms:**
```
bash: ./install-offline.sh: Permission denied
```

**Solution:**
```bash
chmod +x install-offline.sh
./install-offline.sh
```

## Security Considerations

### Credential Management

**Never commit credentials to version control:**

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
```

**Use environment variables or secure vaults:**

```bash
# Good: Environment variables
export DIFY_API_KEY=$(vault read -field=api_key secret/dify)

# Bad: Hardcoded in YAML
# api_key: "dify-123456"  # DON'T DO THIS
```

### Package Verification

**Verify package integrity before deployment:**

```bash
# Generate checksum (online environment)
sha256sum dify-ops-cli-offline-v0.1.0.tar.gz > checksums.txt

# Verify checksum (offline environment)
sha256sum -c checksums.txt
```

### Network Isolation

Confirm the tool makes no external network calls:

```bash
# Test with network monitoring
tcpdump -i any -n host not 10.0.0.0/8 and host not 172.16.0.0/12

# Run dify-ops commands
dify-ops apply config.yaml

# Should only see traffic to your internal Dify API
```

## Maintenance and Updates

### Updating to New Versions

1. **Online Environment**: Build new offline package with updated version
2. **Transfer**: Move new package to offline environment
3. **Offline Environment**: Install new version

```bash
# Remove old version (Docker)
docker rmi dify-ops-cli:v0.1.0

# Load new version
docker load -i dify-ops-cli-v0.2.0.tar.gz

# Or with wheels:
rm -rf .venv
./install-offline.sh  # From new package
```

### Dependency Updates

To update dependencies for security patches:

```bash
# Online environment
cd tools/dify-ops-cli
source .venv/bin/activate

# Update dependencies
uv pip install --upgrade -r requirements.txt

# Regenerate requirements
uv pip freeze | grep -v '^-e' > requirements.txt

# Rebuild offline package
./scripts/build-offline-package.sh
```

## Support

For issues specific to offline deployment:

1. Check this guide's [Troubleshooting](#troubleshooting) section
2. Review the main [README.md](../README.md) for general usage
3. Verify your environment meets all [Prerequisites](#prerequisites)
4. Contact your internal DevOps team for infrastructure issues

## Related Documentation

- [Main README](../README.md) - General usage and features
- [Configuration Examples](../examples/) - Sample YAML configurations
- [Git Worktree Guide](../../../docs/GIT_WORKTREE_GUIDE.md) - Development workflow
