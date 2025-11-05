# NilAI FastAPI + vLLM Upgrade Plan

**Version:** 1.0
**Date:** 2025-11-05
**Branch:** `claude/fastapi-vllm-upgrade-011CUpVeMQWcYMPgodBYFw6U`

## Executive Summary

This plan outlines a comprehensive upgrade of the NilAI FastAPI + vLLM serving platform focusing on:
- **Correctness & Safety** through strict typing and async best practices
- **Maintainability** via clear module boundaries and documentation
- **Performance** with vLLM optimization and benchmarking
- **Security** through hardened defaults and audit tooling
- **Developer Experience** with streamlined tooling and workflows

**Timeline:** Phased approach over 5 stages
**Risk Level:** MEDIUM (production system with public API surface)

---

## Current State Assessment

### Strengths
✅ Async-first architecture with proper context management
✅ Modular design (api/, models/, common/, client/)
✅ Comprehensive CI/CD with GPU testing
✅ Production-ready security (attestation, rate limiting, auth strategies)
✅ `uv` for fast dependency management
✅ Basic ruff and pyright already configured

### Pain Points
🔴 **CRITICAL**: CORS allows all origins (`allow_origins=["*"]`)
🔴 **CRITICAL**: No strict type checking (pyright not in strict mode)
🟡 **HIGH**: vLLM pinned to v0.10.1 (6+ months old)
🟡 **HIGH**: NilRAG runs on CPU in main process (performance bottleneck)
🟡 **MEDIUM**: Missing /healthz and /readyz endpoints
🟡 **MEDIUM**: No pre-commit hooks
🟡 **MEDIUM**: No scripts/Makefile for common workflows
🟡 **MEDIUM**: Missing CONTRIBUTING.md, CODESTYLE.md, SECURITY.md
🟢 **LOW**: No performance benchmarks

### API Surface (Must Preserve)
```
GET  /v1/health              → System health
GET  /v1/models              → List models
GET  /v1/usage               → User usage stats
GET  /v1/attestation/report  → Cryptographic attestation
GET  /v1/delegation          → NilDB delegation tokens
GET  /v1/public_key          → API public key
POST /v1/chat/completions    → Chat completions (streaming + non-streaming)
```

---

## Phased Implementation Strategy

### Phase 1: Guardrails & Tooling (LOW RISK)
**Goal:** Establish development standards without touching production code
**Duration:** 1-2 hours
**Risk:** 🟢 LOW

| Step | Action | Rationale | Risk | Test Impact |
|------|--------|-----------|------|-------------|
| 1.1 | Create `pyrightconfig.json` with strict mode | Catch type errors early; enforce annotations | 🟢 LOW | None (CI only) |
| 1.2 | Enhance `pyproject.toml` [tool.ruff] config | Comprehensive linting; 100 char line length | 🟢 LOW | None (format only) |
| 1.3 | Create `.pre-commit-config.yaml` | Auto-format on commit; prevent bad code | 🟢 LOW | None (local hooks) |
| 1.4 | Create `Makefile` with all workflows | Unified interface for devs; CI consistency | 🟢 LOW | CI must use Makefile |
| 1.5 | Add `scripts/setup.sh` for one-command init | New dev onboarding; reproducible env | 🟢 LOW | None |

**Deliverables:**
- `pyrightconfig.json` (strict mode)
- Updated `pyproject.toml` (ruff config)
- `.pre-commit-config.yaml` (ruff, pyright, detect-secrets)
- `Makefile` (setup, format, lint, typecheck, test, audit, serve, bench)
- `scripts/setup.sh` (install dependencies, create .env, run migrations)

**Acceptance:**
- `make format` runs ruff format
- `make lint` runs ruff check
- `make typecheck` runs pyright
- `make test` runs pytest with coverage
- `make audit` runs pip-audit and bandit
- Pre-commit hooks install and run locally

---

### Phase 2: Type Safety & Contracts (MEDIUM RISK)
**Goal:** Strengthen typing across API surface and internal services
**Duration:** 2-3 hours
**Risk:** 🟡 MEDIUM

| Step | Action | Rationale | Risk | Test Impact |
|------|--------|-----------|------|-------------|
| 2.1 | Add `Annotated` FastAPI dependencies | Explicit dependency types; better IDE support | 🟢 LOW | Unit tests validate deps |
| 2.2 | Strengthen Pydantic v2 models | Constrained types (Field); validated params | 🟡 MEDIUM | May break invalid requests |
| 2.3 | Add vLLM parameter validation | Reject invalid temperature, top_p, max_tokens | 🟡 MEDIUM | Requires boundary tests |
| 2.4 | Type all service functions | Remove `Any`; handle `None` explicitly | 🟢 LOW | Type errors caught in CI |
| 2.5 | Add return types to async handlers | Clarify contracts; enable mypy inference | 🟢 LOW | None (internal change) |

**Deliverables:**
- Updated `nilai_common/types/*.py` with constrained Field types
- Updated `nilai_api/routers/*.py` with Annotated dependencies
- New `nilai_api/validation/*.py` with parameter validators
- Type annotations on all public functions

**Acceptance:**
- `pyright` reports 0 errors
- All Pydantic models use `Field()` with constraints
- Invalid requests return 422 with clear error messages
- Unit tests cover validation edge cases

---

### Phase 3: Security Hardening (HIGH RISK)
**Goal:** Fix CORS, add rate limiting, request size/time limits
**Duration:** 1-2 hours
**Risk:** 🔴 HIGH (changes auth/CORS behavior)

| Step | Action | Rationale | Risk | Test Impact |
|------|--------|-----------|------|-------------|
| 3.1 | **FIX CORS allowlist** | Replace `allow_origins=["*"]` with config | 🔴 HIGH | May break existing clients |
| 3.2 | Add request size limit middleware | Prevent large payload attacks | 🟡 MEDIUM | Requires size limit tests |
| 3.3 | Add request timeout middleware | Prevent long-running abuse | 🟡 MEDIUM | Requires timeout tests |
| 3.4 | Add /healthz (CPU) and /readyz (GPU+engine) | K8s readiness probes; observability | 🟢 LOW | Health checks in tests |
| 3.5 | Add security headers middleware | HSTS, X-Content-Type-Options, etc. | 🟢 LOW | None (header checks) |
| 3.6 | Add `detect-secrets` to pre-commit | Prevent credential leaks | 🟢 LOW | None (local scan) |

**Deliverables:**
- Updated `nilai_api/app.py` with CORS allowlist from config
- New `nilai_api/middleware/security.py` (size, timeout, headers)
- New `/v1/healthz` endpoint (fast CPU check)
- New `/v1/readyz` endpoint (vLLM engine check via discovery)
- `.pre-commit-config.yaml` updated with detect-secrets

**BREAKING CHANGES:**
- CORS now restricted to configured origins (default: ["http://localhost:3000", "http://localhost:8080"])
- Requests >10MB rejected with 413
- Requests >60s timeout with 504

**Mitigation:**
- Add `CORS_ORIGINS` env var for config
- Document in MIGRATION.md
- Add to SECURITY.md

**Acceptance:**
- CORS allowlist enforced (test with curl from invalid origin)
- Requests >10MB rejected (test with large payload)
- Requests >60s timeout (test with sleep endpoint)
- /healthz returns 200 with {"status": "healthy"}
- /readyz returns 200 when engine available, 503 otherwise

---

### Phase 4: Performance & Observability (MEDIUM RISK)
**Goal:** Add benchmarks, optimize hot paths, enhance metrics
**Duration:** 2-3 hours
**Risk:** 🟡 MEDIUM

| Step | Action | Rationale | Risk | Test Impact |
|------|--------|-----------|------|-------------|
| 4.1 | Add `pytest-benchmark` dependency | Measure perf changes; regression detection | 🟢 LOW | New benchmark tests |
| 4.2 | Create benchmark suite | Baseline for streaming, tokenization, validation | 🟡 MEDIUM | Requires mock vLLM |
| 4.3 | Add vLLM tuning defaults in .env | Optimize batching, KV-cache, memory | 🟡 MEDIUM | E2E tests validate |
| 4.4 | Document vLLM config knobs | GPU memory, tensor parallel, batching | 🟢 LOW | None (docs only) |
| 4.5 | Add latency metrics to /v1/chat/completions | Track P50/P95/P99 latency | 🟢 LOW | Prometheus check |

**Deliverables:**
- `tests/benchmarks/test_chat_performance.py` (simple prompt throughput)
- `tests/benchmarks/test_validation_performance.py` (Pydantic overhead)
- Updated `.env.sample` with vLLM tuning vars
- New `docs/VLLM_TUNING.md` with parameter explanations
- Enhanced Prometheus metrics (latency histograms)

**vLLM Tuning Defaults:**
```bash
VLLM_TENSOR_PARALLEL_SIZE=1
VLLM_MAX_NUM_BATCHED_TOKENS=8192
VLLM_MAX_NUM_SEQS=256
VLLM_GPU_MEMORY_UTILIZATION=0.9
VLLM_SWAP_SPACE=4  # GB
VLLM_ENFORCE_EAGER=false
VLLM_DISABLE_LOG_STATS=false
```

**Acceptance:**
- Benchmarks run with `make bench`
- Benchmarks pass in CI (no regression check yet, just collect baseline)
- vLLM env vars documented
- Latency metrics visible in Prometheus

---

### Phase 5: Documentation & DX (LOW RISK)
**Goal:** Complete documentation; streamline developer workflows
**Duration:** 2-3 hours
**Risk:** 🟢 LOW

| Step | Action | Rationale | Risk | Test Impact |
|------|--------|-----------|------|-------------|
| 5.1 | Create CODESTYLE.md | Python patterns, async rules, DTO conventions | 🟢 LOW | None (docs only) |
| 5.2 | Create CONTRIBUTING.md | Workflow, commit style, code review | 🟢 LOW | None (docs only) |
| 5.3 | Create SECURITY.md | Threat model, auth, reporting path, hardening | 🟢 LOW | None (docs only) |
| 5.4 | Create MIGRATION.md | CORS breaking change, upgrade steps | 🟢 LOW | None (docs only) |
| 5.5 | Update README.md | 10-minute quickstart, GPU prereqs | 🟢 LOW | None (docs only) |
| 5.6 | Create CHANGESUMMARY.md | Grouped by category | 🟢 LOW | None (docs only) |

**Deliverables:**
- `CODESTYLE.md` (Python 3.12+, async patterns, error handling, testing)
- `CONTRIBUTING.md` (setup, commit style, PR workflow, release versioning)
- `SECURITY.md` (threat model, prompt injection notes, secrets hygiene)
- `MIGRATION.md` (v0.1.0 → v0.2.0 breaking changes)
- Updated `README.md` (quickstart, GPU setup)
- `CHANGESUMMARY.md` (summary of all changes)

**Acceptance:**
- All docs render correctly in GitHub
- README quickstart works from scratch
- CONTRIBUTING.md covers all dev workflows

---

## CI/CD Updates

### Enhanced Workflow Structure
```yaml
jobs:
  lint:          # ruff format + ruff check
  typecheck:     # pyright strict
  audit:         # pip-audit + bandit (high/critical only)
  test-unit:     # pytest tests/unit (parallel)
  test-integration: # pytest tests/integration
  benchmark:     # pytest tests/benchmarks (collect baseline)
  build:         # Docker builds (GPU runner)
  test-e2e:      # E2E tests (GPU runner)
  push:          # Push to ECR (main/release only)
```

### Key Improvements
- ✅ Separate lint/typecheck/audit jobs (faster feedback)
- ✅ Parallel unit test execution (matrix by module)
- ✅ Cache uv dependencies (faster runs)
- ✅ Security audit must pass (high/critical = fail)
- ✅ Benchmark baseline collection (no regression check yet)

---

## Risk Assessment Summary

### HIGH RISK Changes
1. **CORS Allowlist** → May break existing clients
   - **Mitigation:** Env var config; document in MIGRATION.md; add to SECURITY.md

### MEDIUM RISK Changes
1. **Pydantic v2 Validation** → May reject previously accepted requests
   - **Mitigation:** Comprehensive boundary tests; clear 422 error messages
2. **Request Size/Timeout Limits** → May break long-running or large requests
   - **Mitigation:** Configurable limits; document in API docs

### LOW RISK Changes
- All tooling, docs, and internal refactors

---

## Rollback Plan

If issues arise in production:

1. **CORS Issues:** Revert to `allow_origins=["*"]` temporarily via env var
2. **Validation Issues:** Add bypass flag for specific clients
3. **Performance Regression:** Revert vLLM config changes
4. **Type Errors:** Downgrade pyright strictness temporarily

**Emergency Rollback Command:**
```bash
git revert <commit-sha>
make test && make lint && make typecheck
git push -u origin <branch>
```

---

## Success Criteria Checklist

### Correctness & Safety
- [ ] `pyright` reports 0 errors in strict mode
- [ ] All Pydantic models use Field() with constraints
- [ ] Invalid vLLM params rejected with 422
- [ ] All async code is non-blocking (no blocking I/O in handlers)

### Maintainability
- [ ] CODESTYLE.md, CONTRIBUTING.md, SECURITY.md created
- [ ] All public functions have docstrings
- [ ] Module boundaries clear (api/, core/, models/, services/, infra/, tests/)

### Performance
- [ ] Benchmarks run with `make bench`
- [ ] vLLM tuning defaults documented and tested
- [ ] Latency metrics added to Prometheus

### Security
- [ ] CORS allowlist enforced
- [ ] Request size/timeout limits active
- [ ] `pip-audit` and `bandit` pass (high/critical = 0)
- [ ] `detect-secrets` in pre-commit hooks
- [ ] Security headers middleware active

### Developer Experience
- [ ] `make setup` works from scratch
- [ ] `make format && make lint && make typecheck && make test` passes
- [ ] Pre-commit hooks install and run
- [ ] CI green on all jobs
- [ ] README quickstart works in <10 minutes

### Coverage & Testing
- [ ] Changed code coverage ≥ 80%
- [ ] Streaming and error paths tested
- [ ] Boundary validation tests (temperature, top_p, max_tokens)
- [ ] Health check endpoints tested

---

## Timeline Estimate

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 1: Guardrails & Tooling | 1-2h | 2h |
| Phase 2: Type Safety | 2-3h | 5h |
| Phase 3: Security Hardening | 1-2h | 7h |
| Phase 4: Performance | 2-3h | 10h |
| Phase 5: Documentation | 2-3h | 13h |
| **Buffer for Issues** | +3h | **16h** |

**Total Estimated Time:** 13-16 hours

---

## Dependencies & Prerequisites

### Required Tools (Already Present)
✅ Python 3.12+
✅ uv (Astral package manager)
✅ ruff (formatter + linter)
✅ pyright (type checker)
✅ pytest (test runner)

### New Dependencies to Add
- `pytest-benchmark` (performance testing)
- `bandit` (security linting)
- `pip-audit` (dependency vulnerability scanning)
- `detect-secrets` (pre-commit hook)

### Infrastructure
- Redis (already configured)
- PostgreSQL (already configured)
- vLLM Docker image (already built)
- GPU runner (already in CI/CD)

---

## Open Questions & Future Work

### Deferred to Future Iterations
1. **vLLM Upgrade to Latest** (v0.10.1 → v0.6+)
   - Requires testing with all models
   - May need template updates
   - Breaking changes in API

2. **NilRAG GPU Service Extraction**
   - Move embeddings to separate GPU container
   - Upgrade to better embedding model
   - Requires infra changes

3. **Async Batch Database Writes**
   - Optimize query logging throughput
   - Requires careful transaction handling

4. **Load Testing Suite**
   - Locust or k6 for realistic load
   - GPU resource profiling
   - Requires dedicated test environment

### Questions for Product/Eng Team
- **CORS Origins:** What domains should be allowlisted in production?
- **Request Limits:** Are 10MB size / 60s timeout acceptable?
- **vLLM Upgrade:** What's the priority for updating to latest vLLM?
- **Breaking Changes:** Is v0.1.0 → v0.2.0 semver bump acceptable?

---

## Appendix: File Changes Overview

### New Files (15)
```
.pre-commit-config.yaml
pyrightconfig.json
Makefile
scripts/setup.sh
CODESTYLE.md
CONTRIBUTING.md
SECURITY.md
MIGRATION.md
CHANGESUMMARY.md
docs/VLLM_TUNING.md
tests/benchmarks/test_chat_performance.py
tests/benchmarks/test_validation_performance.py
nilai_api/middleware/security.py
nilai_api/validation/vllm_params.py
```

### Modified Files (8)
```
pyproject.toml                        # ruff config
nilai-api/pyproject.toml              # pytest-benchmark dep
nilai_api/app.py                      # CORS, middleware, health endpoints
nilai_api/routers/private.py          # Annotated deps, validation
nilai_api/routers/public.py           # health endpoints
nilai_common/types/*.py               # constrained Pydantic models
.github/workflows/cicd.yml            # enhanced workflow
README.md                             # quickstart updates
```

---

**Plan Approved By:** AI Senior Staff Engineer
**Next Step:** Begin Phase 1 - Guardrails & Tooling
