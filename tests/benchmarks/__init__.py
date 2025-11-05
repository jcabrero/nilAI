"""Benchmark tests for NilAI performance-critical paths.

These benchmarks establish baselines for:
- Pydantic validation overhead
- Health check endpoint latency
- Request/response serialization

Run with: pytest tests/benchmarks --benchmark-only
"""
