# Migration Guide: v0.1.0 → v0.2.0

**Release Date:** TBD
**Severity:** MEDIUM (One breaking change: CORS configuration)

This guide helps you migrate from NilAI v0.1.0 to v0.2.0, which includes security hardening, improved tooling, and comprehensive documentation.

---

## Table of Contents

1. [Summary of Changes](#summary-of-changes)
2. [Breaking Changes](#breaking-changes)
3. [New Features](#new-features)
4. [Migration Steps](#migration-steps)
5. [Testing Your Migration](#testing-your-migration)
6. [Rollback Instructions](#rollback-instructions)
7. [FAQ](#faq)

---

## Summary of Changes

### What Changed
- **BREAKING:** CORS now uses allowlist instead of wildcard (`["*"]`)
- **NEW:** Health check endpoints (`/healthz`, `/readyz`) for Kubernetes
- **NEW:** Security middleware (request size/timeout limits, security headers)
- **NEW:** Comprehensive documentation (PLAN, CODESTYLE, CONTRIBUTING, SECURITY)
- **NEW:** Development tooling (Makefile, enhanced pre-commit hooks, benchmarks)
- **IMPROVED:** Type checking with pyrightconfig.json
- **IMPROVED:** Linting with comprehensive ruff configuration

### Impact Assessment
- **Users:** Must configure `CORS_ORIGINS` environment variable
- **CI/CD:** No changes required (backward compatible)
- **Database:** No schema changes
- **API:** No endpoint changes (only new endpoints added)

---

## Breaking Changes

### 1. CORS Configuration (CRITICAL)

**⚠️ ACTION REQUIRED**

#### What Changed
```python
# Before (v0.1.0)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows ALL origins (security risk)
    ...
)

# After (v0.2.0)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")
allowed_origins = [origin.strip() for origin in CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Allowlist only
    ...
)
```

#### Why This Changed
**Security:** Wildcard CORS (`allow_origins=["*"]`) allows any website to make requests to your API, enabling:
- Cross-origin attacks
- Data exfiltration
- Unauthorized API access from malicious sites

#### Who Is Affected
- **Production deployments** with web frontends
- **Staging environments** accessed from web browsers
- **Development environments** with frontend applications

#### Migration Required
✅ **Yes** - You must set the `CORS_ORIGINS` environment variable

---

## Migration Steps

### Step 1: Identify Your Origins

List all domains that need to access your API:

```bash
# Development
http://localhost:3000
http://localhost:8080
http://127.0.0.1:3000

# Staging
https://staging.example.com
https://staging-app.example.com

# Production
https://app.example.com
https://dashboard.example.com
https://example.com
```

### Step 2: Set Environment Variable

#### For Docker / Docker Compose

Add to your `docker-compose.yml`:

```yaml
services:
  api:
    environment:
      - CORS_ORIGINS=https://app.example.com,https://dashboard.example.com
```

Or in `.env` file:

```bash
# Production CORS origins (comma-separated, no spaces)
CORS_ORIGINS=https://app.example.com,https://dashboard.example.com

# Development CORS origins
# CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

#### For Kubernetes

Add to ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nilai-config
data:
  CORS_ORIGINS: "https://app.example.com,https://dashboard.example.com"
```

Or set in Deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nilai-api
spec:
  template:
    spec:
      containers:
        - name: api
          env:
            - name: CORS_ORIGINS
              value: "https://app.example.com,https://dashboard.example.com"
```

#### For Systemd Services

Add to service file `/etc/systemd/system/nilai-api.service`:

```ini
[Service]
Environment="CORS_ORIGINS=https://app.example.com,https://dashboard.example.com"
```

#### For Direct Python Execution

Set before running:

```bash
export CORS_ORIGINS="http://localhost:3000,http://localhost:8080"
python -m nilai_api
```

### Step 3: Update Configuration Management

If using configuration management tools:

**Ansible:**
```yaml
- name: Set CORS origins
  lineinfile:
    path: /opt/nilai/.env
    regexp: '^CORS_ORIGINS='
    line: 'CORS_ORIGINS=https://app.example.com,https://dashboard.example.com'
```

**Terraform:**
```hcl
resource "aws_ecs_task_definition" "nilai" {
  container_definitions = jsonencode([{
    environment = [
      {
        name  = "CORS_ORIGINS"
        value = "https://app.example.com,https://dashboard.example.com"
      }
    ]
  }])
}
```

### Step 4: Deploy and Verify

1. **Update configuration** (add `CORS_ORIGINS`)
2. **Deploy new version** (v0.2.0)
3. **Verify CORS works** (see testing section below)

---

## Testing Your Migration

### Test 1: Verify Allowed Origins

```bash
# Test from allowed origin (should succeed)
curl -H "Origin: https://app.example.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://api.example.com/v1/health

# Expected: Should include CORS headers
# Access-Control-Allow-Origin: https://app.example.com
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
```

### Test 2: Verify Blocked Origins

```bash
# Test from disallowed origin (should fail CORS)
curl -H "Origin: https://evil.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     https://api.example.com/v1/health

# Expected: No Access-Control-Allow-Origin header
# Browser would block this request
```

### Test 3: Browser Console Test

Open browser console on your frontend:

```javascript
// Should succeed
fetch('https://api.example.com/v1/health', {
  method: 'GET',
  headers: { 'Content-Type': 'application/json' }
})
.then(r => r.json())
.then(console.log)
.catch(console.error);
```

If you see CORS errors in console:
```
Access to fetch at 'https://api.example.com/v1/health' from origin 'https://your-frontend.com'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present.
```

**Solution:** Add `https://your-frontend.com` to `CORS_ORIGINS`

### Test 4: New Health Endpoints

```bash
# Test new /healthz endpoint (fast liveness check)
curl https://api.example.com/healthz
# Expected: {"status": "healthy", "uptime": "123.45s"}

# Test new /readyz endpoint (readiness check)
curl https://api.example.com/readyz
# Expected: {"status": "ready", "checks": {"models": "ok", "state": "ok"}}
# Or 503 if models not ready: {"status": "not_ready", "reason": "..."}
```

---

## New Features (Non-Breaking)

These features are automatically available after upgrading:

### 1. Health Check Endpoints

**`GET /healthz`** - Fast liveness probe
- Returns immediately (< 10ms)
- No dependency checks
- Use for Kubernetes liveness probes

**`GET /readyz`** - Comprehensive readiness probe
- Checks model availability
- Checks state management
- Returns 503 if not ready
- Use for Kubernetes readiness probes

#### Kubernetes Configuration

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: nilai-api
      livenessProbe:
        httpGet:
          path: /healthz
          port: 8080
        initialDelaySeconds: 10
        periodSeconds: 30

      readinessProbe:
        httpGet:
          path: /readyz
          port: 8080
        initialDelaySeconds: 15
        periodSeconds: 10
```

### 2. Security Middleware

Automatically enabled (no configuration required):

- **Request Size Limit:** Max 10MB (configurable via `MAX_REQUEST_SIZE`)
- **Request Timeout:** 60 seconds (configurable via `REQUEST_TIMEOUT`)
- **Security Headers:**
  - `Strict-Transport-Security` (HSTS)
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`

#### Configure Limits (Optional)

```bash
# .env
MAX_REQUEST_SIZE=20971520  # 20MB in bytes
REQUEST_TIMEOUT=120  # 120 seconds
```

### 3. Development Tooling

**Makefile commands:**
```bash
make setup      # One-command setup
make format     # Format with ruff
make lint       # Lint with ruff
make typecheck  # Type check with pyright
make test       # Run all tests
make audit      # Security audits
make serve      # Start dev server
make ci         # Run all CI checks
```

**Pre-commit hooks:**
- Automatic formatting (ruff)
- Linting (ruff)
- Type checking (pyright)
- Secret detection (detect-secrets)

Install with: `make pre-commit-install`

---

## Rollback Instructions

If you need to rollback to v0.1.0:

### Option 1: Temporary Fix (Keep v0.2.0, Restore Wildcard)

**⚠️ ONLY FOR EMERGENCY - NOT SECURE**

```bash
# Set CORS to wildcard (temporary workaround)
export CORS_ORIGINS="*"
```

This restores the old behavior but maintains the security risk.

### Option 2: Full Rollback (Revert to v0.1.0)

```bash
# Revert to previous Docker image
docker pull your-registry/nilai-api:v0.1.0
docker-compose up -d

# Or revert Git commit
git revert <v0.2.0-commit-sha>
git push
```

### Option 3: Gradual Migration

Deploy v0.2.0 with permissive CORS temporarily:

```bash
# Phase 1: Deploy with permissive CORS
CORS_ORIGINS="*"

# Phase 2: Gradually restrict
CORS_ORIGINS="*,https://app.example.com,https://dashboard.example.com"

# Phase 3: Remove wildcard
CORS_ORIGINS="https://app.example.com,https://dashboard.example.com"
```

---

## FAQ

### Q: What happens if I don't set CORS_ORIGINS?

**A:** The API will use default development origins:
- `http://localhost:3000`
- `http://localhost:8080`

This is safe for development but will break production frontends.

### Q: Can I use wildcard subdomains?

**A:** No, the CORS middleware does not support wildcards like `https://*.example.com`.

You must list each subdomain explicitly:
```bash
CORS_ORIGINS=https://app.example.com,https://api.example.com,https://dashboard.example.com
```

### Q: How do I allow multiple environments?

**A:** Use environment-specific configuration:

```bash
# Development
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Staging
CORS_ORIGINS=https://staging-app.example.com,https://staging-dashboard.example.com

# Production
CORS_ORIGINS=https://app.example.com,https://dashboard.example.com
```

### Q: Does this affect API clients (non-browser)?

**A:** No. CORS only affects web browsers. API clients (Python, cURL, Postman, etc.) are not affected.

### Q: Can I disable CORS entirely?

**A:** Not recommended. If absolutely necessary for internal networks only:

```python
# Custom code (not recommended)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # UNSAFE
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Q: What if my frontend is on a dynamic port?

**A:** For development, allow a range:

```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:8080
```

For production, use a fixed domain.

### Q: Do I need to restart the application?

**A:** Yes. Environment variables are read at startup. After changing `CORS_ORIGINS`:

```bash
# Docker Compose
docker-compose restart api

# Kubernetes
kubectl rollout restart deployment/nilai-api

# Systemd
systemctl restart nilai-api
```

---

## Support

If you encounter issues during migration:

1. **Check logs:**
   ```bash
   # Docker
   docker-compose logs api

   # Kubernetes
   kubectl logs deployment/nilai-api

   # Systemd
   journalctl -u nilai-api -f
   ```

2. **Verify configuration:**
   ```bash
   # Check if CORS_ORIGINS is set
   docker-compose exec api env | grep CORS_ORIGINS

   # Or in container
   echo $CORS_ORIGINS
   ```

3. **Test with verbose output:**
   ```bash
   curl -v -H "Origin: https://app.example.com" https://api.example.com/v1/health
   ```

4. **Contact support:**
   - Email: jose.cabrero@nillion.com
   - GitHub Issues: https://github.com/jcabrero/nilAI/issues

---

**Last Updated:** 2025-11-05
**Version:** 1.0
**Covers Migration:** v0.1.0 → v0.2.0
