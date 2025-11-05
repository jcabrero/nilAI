# nilAI

**An AI model serving platform powered by secure, confidential computing.**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![vLLM](https://img.shields.io/badge/vLLM-0.10+-orange.svg)](https://github.com/vllm-project/vllm)

---

## 🚀 Quick Start (10 Minutes)

```bash
# 1. Clone the repository
git clone https://github.com/jcabrero/nilAI.git
cd nilAI

# 2. Set up development environment
make setup

# 3. Configure environment
cp .env.sample .env
# Edit .env with your Hugging Face token and other settings

# 4. Run database migrations
make migration-upgrade

# 5. Start development server
make serve
```

Your API is now running at `http://localhost:8080`

**Test it:**
```bash
curl http://localhost:8080/healthz
# {"status": "healthy", "uptime": "5.23s"}
```

**View API docs:** http://localhost:8080/docs

---

## 📚 Documentation

- **[PLAN.md](./PLAN.md)** - Phased upgrade strategy and roadmap
- **[CODESTYLE.md](./CODESTYLE.md)** - Python code standards and best practices
- **[CONTRIBUTING.md](./CONTRIBUTING.md)** - How to contribute (setup, workflow, PR process)
- **[SECURITY.md](./SECURITY.md)** - Security threat model and hardening guide
- **[MIGRATION.md](./MIGRATION.md)** - Migration guide for v0.1.0 → v0.2.0

---

## Overview

nilAI is a production-ready platform designed to run on Confidential VMs with Trusted Execution Environments (TEEs). It ensures secure deployment and management of multiple AI models across different environments, providing a unified API interface with:

- ✅ **Cryptographic attestation** for service verification
- ✅ **Multi-strategy authentication** (API keys, NUC tokens)
- ✅ **Rate limiting** and request validation
- ✅ **Streaming support** with EventSource
- ✅ **Tool calling** (Python code execution)
- ✅ **Web search integration** (Brave API)
- ✅ **Vector RAG** (NilRAG)

## Prerequisites

- Docker
- Docker Compose
- Hugging Face API Token (for accessing certain models)

## Configuration

1. **Environment Setup**
   - Copy the `.env.sample` file to `.env`
   ```shell
   cp .env.sample .env
   ```
   - Update the environment variables in `.env`:
     - `HUGGINGFACE_API_TOKEN`: Your Hugging Face API token
   - Obtain token by requesting access on the specific model's Hugging Face page. For example, to request access for the Llama 1B model, you can ask [here](https://huggingface.co/meta-llama/Llama-3.2-1B). Note that for the Llama-8B model, you need to make a separate request.

## Deployment Options

### 1. Docker Compose Deployment (Recommended)

#### Development Environment
```shell
# Build nilai_attestation endpoint
docker build -t nillion/nilai-attestation:latest -f docker/attestation.Dockerfile .
# Build vLLM docker container
docker build -t nillion/nilai-vllm:latest -f docker/vllm.Dockerfile .
# Build nilai_api container
docker build -t nillion/nilai-api:latest -f docker/api.Dockerfile --target nilai .
```
Then, to deploy:

```shell

# Deploy with CPU-only configuration
docker compose -f docker-compose.yml \
  -f docker-compose.dev.yml \
  -f docker/compose/docker-compose.llama-1b-gpu.yml \
  up -d

# Monitor logs
docker compose -f docker-compose.yml \
  -f docker-compose.dev.yml \
  -f docker/compose/docker-compose.llama-1b-gpu.yml \
  logs -f
```

#### Production Environment
```shell
# Build nilai_attestation endpoint
docker build -t nillion/nilai-attestation:latest -f docker/attestation.Dockerfile .
# Build vLLM docker container
docker build -t nillion/nilai-vllm:latest -f docker/vllm.Dockerfile .
# Build nilai_api container
docker build -t nillion/nilai-api:latest -f docker/api.Dockerfile --target nilai .
```
To deploy:
```shell
docker compose -f docker-compose.yml \
-f docker-compose.prod.yml \
-f docker/compose/docker-compose.llama-3b-gpu.yml \
-f docker/compose/docker-compose.llama-8b-gpu.yml \
up -d
```
**Note**: Remove lines for models you do not wish to deploy.

#### Testing Without GPU

```shell
# Build nilai_attestation endpoint
docker build -t nillion/nilai-attestation:latest -f docker/attestation.Dockerfile .
# Build vLLM docker container
docker build -t nillion/nilai-vllm:latest -f docker/vllm.Dockerfile .
# Build nilai_api container
docker build -t nillion/nilai-api:latest -f docker/api.Dockerfile --target nilai --platform linux/amd64 .
```
To deploy:
```shell

python3 ./scripts/docker-composer.py --dev -f docker/compose/docker-compose.llama-1b-cpu.yml -o development-compose.yml

docker compose -f development-compose.yml up -d
```

### 2. Using the Docker Compose Helper Script

For easier management of multiple compose files and image substitutions, use the `docker-composer.py` script:

#### Basic Usage

```shell
# Generate a composed configuration for development
python3 ./scripts/docker-composer.py --dev -o dev-compose.yml

# Generate a composed configuration for production
python3 ./scripts/docker-composer.py --prod -o prod-compose.yml

# Include specific model configurations
python3 ./scripts/docker-composer.py --prod \
  -f docker-compose.llama-3b-gpu.yml \
  -f docker-compose.llama-8b-gpu.yml \
  -o production-compose.yml
```

#### Image Substitution

Replace default images with custom ones (useful for production deployments with specific image versions):

```shell
# Production example with custom ECR images
python3 ./scripts/docker-composer.py --prod \
  -f docker-compose.llama-3b-gpu.yml \
  --image 'nillion/nilai-api:latest=public.ecr.aws/k5d9x2g2/nilai-api:v0.1.0-rc1' \
  --image 'nillion/nilai-vllm:latest=public.ecr.aws/k5d9x2g2/nilai-vllm:v0.1.0-rc1' \
  --image 'nillion/nilai-attestation:latest=public.ecr.aws/k5d9x2g2/nilai-attestation:v0.1.0-rc1' \
  -o production-compose.yml

# Then deploy with the generated file
docker compose -f production-compose.yml up -d
```

#### Script Options

- `--dev`: Include development-specific configurations
- `--prod`: Include production-specific configurations
- `-f, --file <filename>`: Include additional compose files from `docker/compose/` directory
- `-o, --output <filename>`: Specify output filename (default: `output.yml`)
- `--image <old=new>`: Substitute Docker images (can be used multiple times)
- `-h, --help`: Show help message

#### Production Deployment Example

For a complete production setup with custom images:

```shell
# 1a. Generate the Production 1 image
python3 ./scripts/docker-composer.py --prod \
  -f docker/compose/docker-compose.nilai-prod-1.yml \
  --image 'nillion/nilai-api:latest=public.ecr.aws/k5d9x2g2/nilai-api:v0.2.0-alpha2' \
  --image 'nillion/nilai-vllm:latest=public.ecr.aws/k5d9x2g2/nilai-vllm:v0.2.0-alpha2' \
  --image 'nillion/nilai-attestation:latest=public.ecr.aws/k5d9x2g2/nilai-attestation:v0.2.0-alpha2' \
  --testnet \
  -o production-compose.yml

# 1b. Generate the Production 2 image
python3 ./scripts/docker-composer.py --prod \
  -f docker/compose/docker-compose.nilai-prod-2.yml \
  --image 'nillion/nilai-api:latest=public.ecr.aws/k5d9x2g2/nilai-api:v0.2.0-alpha2' \
  --image 'nillion/nilai-vllm:latest=public.ecr.aws/k5d9x2g2/nilai-vllm:v0.2.0-alpha2' \
  --image 'nillion/nilai-attestation:latest=public.ecr.aws/k5d9x2g2/nilai-attestation:v0.2.0-alpha2' \
  -o production-compose.yml


# 2. Deploy using the generated file
docker compose -f production-compose.yml up -d

# 3. Monitor logs
docker compose -f production-compose.yml logs -f
```

## Developer Workflow

### Code Quality and Formatting

Install pre-commit hooks to automatically format code and run checks:

```shell
uv run pre-commit install
```

## Model Lifecycle Management

- Models register themselves in the Redis Discovery database
- Registration includes address information with an auto-expiring lifetime
- If a model disconnects, it is automatically removed from the available models

## Security

- Hugging Face API token controls model access
- PostgreSQL database manages user permissions
- Distributed architecture allows for flexible security configurations

## Troubleshooting

Common issues and solutions:

1. **Container Logs**
   ```shell
   # View logs for all services
   docker compose logs -f

   # View logs for specific service
   docker compose logs -f api
   ```

2. **Database Connection**
   ```shell
   # Check PostgreSQL connection
   docker exec -it postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
   ```

3. **Service Health**
   ```shell
   # Check service health status
   docker compose ps
   ```

### vLLM for Local Execution on macOS
To configure vLLM for **local execution on macOS**, execute the following steps:
```shell
# Clone vLLM repository (root folder)
git clone https://github.com/vllm-project/vllm.git
cd vllm
git checkout v0.10.1 # We use v0.10.1
# Build vLLM OpenAI (vllm folder)
docker build -f Dockerfile.arm -t vllm/vllm-openai . --shm-size=4g

# Build nilai attestation container (root folder)
docker build -t nillion/nilai-attestation:latest -f docker/attestation.Dockerfile .
# Build vLLM docker container (root folder)
docker build -t nillion/nilai-vllm:latest -f docker/vllm.Dockerfile .
# Build nilai_api container
docker build -t nillion/nilai-api:latest -f docker/api.Dockerfile --target nilai --platform linux/amd64 .
````

## Contributing

1. Fork the repository
2. Create a feature branch
3. Install pre-commit hooks
4. Make your changes
5. Submit a pull request

## License

[Add your project's license information here]
