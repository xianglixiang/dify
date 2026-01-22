# Dify Operations CLI

A command-line tool for automating Dify platform operations, including tenant management, plugin installation, and model configuration.

## Features

- **Tenant Management**: Create and manage tenants/workspaces
- **Plugin Management**: Upload and install plugins in batch
- **Model Configuration**: Configure model providers and their credentials
- **Configuration-as-Code**: Define infrastructure using YAML files
- **Idempotent Operations**: Safe to run multiple times
- **CI/CD Ready**: Easy integration with automation pipelines

## Installation

### Using uv (Recommended)

```bash
# From the project directory
cd tools/dify-ops-cli

# Install in development mode
uv pip install -e .

# Or install from git
uv pip install git+https://github.com/your-org/dify.git#subdirectory=tools/dify-ops-cli
```

### Using pip

```bash
cd tools/dify-ops-cli
pip install -e .
```

## Quick Start

### 1. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your credentials
DIFY_API_URL=http://localhost:5001
DIFY_API_KEY=your-api-key
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Create a Configuration File

Create a `config.yaml` file:

```yaml
version: "1.0"

connection:
  api_url: "${DIFY_API_URL}"
  api_key: "${DIFY_API_KEY}"

tenants:
  - name: "My Workspace"
    email: "admin@example.com"
    language: "en-US"

options:
  idempotent: true
```

### 3. Run the CLI

```bash
# Validate your configuration
dify-ops config validate config.yaml

# View parsed configuration
dify-ops config show config.yaml

# Preview changes (dry-run) before applying
dify-ops apply config.yaml --dry-run

# Apply complete configuration from YAML file
dify-ops apply config.yaml

# Or use individual commands:
# Create a tenant
dify-ops tenant create --email admin@example.com --name "My Workspace"

# List all tenants
dify-ops tenant list
```

## Configuration

### Configuration File Format

The configuration file uses YAML format with the following structure:

```yaml
version: "1.0"  # Required: configuration version

metadata:  # Optional
  name: "Setup Name"
  description: "Setup description"

connection:  # Required
  api_url: "http://localhost:5001"
  api_key: "${DIFY_API_KEY}"
  timeout: 300
  verify_ssl: true

tenants:  # Required
  - name: "Workspace Name"
    email: "owner@example.com"
    language: "en-US"

    model_providers:  # Optional
      - provider: "openai"
        credentials:
          openai_api_key: "${OPENAI_API_KEY}"
        models:
          - model: "gpt-4o"
            model_type: "llm"
            enabled: true

    plugins:  # Optional
      - source: "local"
        path: "./plugins/my-plugin.difypkg"
        install: true

    default_model:  # Optional
      provider: "openai"
      model: "gpt-4o"
      model_type: "llm"

options:  # Optional
  idempotent: true
  fail_fast: false
  max_retries: 3
  retry_delay: 5
  dry_run: false
```

### Environment Variables

Environment variables can be used in configuration files using the `${VAR_NAME}` syntax:

```yaml
connection:
  api_key: "${DIFY_API_KEY}"

tenants:
  - model_providers:
      - credentials:
          openai_api_key: "${OPENAI_API_KEY}"
```

## CLI Commands

### Apply Command (Recommended)

The `apply` command is the main way to configure Dify using YAML files. It orchestrates all operations:

```bash
# Preview changes without applying (dry-run)
dify-ops apply config.yaml --dry-run

# Apply complete configuration
dify-ops apply config.yaml

# Apply with fail-fast mode (stop on first error)
dify-ops apply config.yaml --fail-fast

# Verbose output for debugging
dify-ops -v apply config.yaml
```

**What the apply command does:**
1. Creates tenants/workspaces (with idempotent support)
2. Configures model providers and credentials
3. Enables/disables models
4. Uploads and installs plugins
5. Sets default models

**Features:**
- **Dry-run mode**: Preview changes before applying
- **Idempotent**: Safe to run multiple times
- **Fail-fast option**: Stop on first error or continue
- **Progress tracking**: Real-time status updates
- **Error handling**: Detailed error messages and retries

### Configuration Commands

```bash
# Validate a configuration file
dify-ops config validate <config-file>

# Show parsed configuration
dify-ops config show <config-file>
```

### Tenant Commands

```bash
# Create a new tenant
dify-ops tenant create \
  --api-url http://localhost:5001 \
  --api-key your-key \
  --email admin@example.com \
  --name "My Workspace"

# List all tenants
dify-ops tenant list \
  --api-url http://localhost:5001 \
  --api-key your-key
```

Environment variables can be used instead of command-line arguments:

```bash
export DIFY_API_URL=http://localhost:5001
export DIFY_API_KEY=your-key

dify-ops tenant create --email admin@example.com --name "My Workspace"
dify-ops tenant list
```

### Plugin Commands

```bash
# Upload a plugin package
dify-ops plugin upload path/to/plugin.difypkg

# Upload and install a plugin
dify-ops plugin upload path/to/plugin.difypkg --no-wait

# Upload without installing
dify-ops plugin upload path/to/plugin.difypkg --no-install

# Install a plugin by ID
dify-ops plugin install <plugin-id>

# Batch upload and install multiple plugins
dify-ops plugin batch-install \
  plugin1.difypkg \
  plugin2.difypkg \
  plugin3.difypkg

# List installed plugins
dify-ops plugin list

# Check plugin installation task status
dify-ops plugin task-status <task-id>
```

### Model Commands

```bash
# Add a model provider with credentials
dify-ops model add-provider openai \
  -c openai_api_key=sk-your-key-here

dify-ops model add-provider anthropic \
  -c anthropic_api_key=sk-ant-your-key-here

# Enable a model for a provider
dify-ops model enable openai gpt-4o --model-type llm
dify-ops model enable openai text-embedding-3-large --model-type text-embedding

# Disable a model
dify-ops model disable openai gpt-3.5-turbo --model-type llm

# Set default model for the workspace
dify-ops model set-default openai gpt-4o --model-type llm

# List all model providers
dify-ops model list-providers

# List models for a specific provider
dify-ops model list-models openai

# Get current default model
dify-ops model get-default
```

## Examples

See the `examples/` directory for configuration examples:

- [`basic-setup.yaml`](./examples/basic-setup.yaml): Minimal configuration for creating a tenant
- [`plugin-setup.yaml`](./examples/plugin-setup.yaml): Plugin upload and installation example
- [`model-setup.yaml`](./examples/model-setup.yaml): Model provider and model configuration example
- [`complete-setup.yaml`](./examples/complete-setup.yaml): Full configuration with models and plugins

## Development

### Project Structure

```
dify-ops-cli/
├── dify_ops_cli/          # Main package
│   ├── client/            # HTTP client and exceptions
│   ├── config/            # Configuration schema and loader
│   ├── services/          # Business logic services
│   └── utils/             # Utility functions
├── examples/              # Configuration examples
├── tests/                 # Test suite
└── docs/                  # Documentation
```

### Running Tests

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=dify_ops_cli --cov-report=term-missing

# Run type checking
basedpyright

# Run linting
ruff check .

# Auto-fix linting issues
ruff check --fix .
```

### Code Quality

The project uses:

- **pytest**: Testing framework
- **basedpyright**: Type checking
- **ruff**: Fast linting and formatting
- **pydantic**: Configuration validation

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy Dify
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install uv
        run: pip install uv

      - name: Install dify-ops-cli
        run: |
          cd tools/dify-ops-cli
          uv pip install .

      - name: Apply configuration
        env:
          DIFY_API_KEY: ${{ secrets.DIFY_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: dify-ops apply config/production.yaml
```

## Roadmap

### Phase 1 (Completed)
- ✅ Basic tenant management
- ✅ Configuration validation
- ✅ CLI commands

### Phase 2 (Completed)
- ✅ Plugin upload and installation
- ✅ Batch plugin operations
- ✅ Task status monitoring
- ✅ Progress display

### Phase 3 (Completed)
- ✅ Model provider configuration
- ✅ Model enablement/disablement
- ✅ Default model setting
- ✅ Provider and model listing

### Phase 4 (Completed)
- ✅ Complete `apply` command
- ✅ Orchestrated configuration
- ✅ Dry-run mode
- ✅ Idempotent execution
- ✅ Error handling and retries
- ✅ Progress tracking and summary

### Phase 5 (Future)
- [ ] Configuration export
- [ ] Configuration diff
- [ ] Web UI
- [ ] Webhook integration

## Contributing

Contributions are welcome! Please follow these steps:

1. Create a feature branch from `dev`
2. Make your changes
3. Write tests for your changes
4. Run tests and linting
5. Submit a pull request

See the main Dify repository's [TEAM_WORKFLOW.md](../../docs/TEAM_WORKFLOW.md) for detailed contribution guidelines.

## License

This project is part of the Dify platform and follows the same license.

## Support

- Documentation: See the `docs/` directory
- Issues: Report bugs in the main Dify repository
- Team Discussion: Use the team's communication channels

## Related Documentation

- [Git Worktree Guide](../../docs/GIT_WORKTREE_GUIDE.md)
- [Team Workflow](../../docs/TEAM_WORKFLOW.md)
- [Dify Official Documentation](https://docs.dify.ai/)
