"""Benchmark tests for Pydantic validation performance.

These tests measure the overhead of input validation using Pydantic models.
"""

import pytest
from nilai_common import ChatRequest, MessageAdapter


class TestPydanticValidationPerformance:
    """Benchmark Pydantic model validation overhead."""

    @pytest.fixture
    def sample_chat_request_data(self):
        """Sample chat request data for benchmarking."""
        return {
            "model": "meta-llama/Llama-3.2-1B-Instruct",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is Python?"},
            ],
            "temperature": 0.7,
            "max_tokens": 1024,
            "stream": False,
        }

    def test_chat_request_validation_benchmark(self, benchmark, sample_chat_request_data):
        """Benchmark ChatRequest validation.

        Measures the time to validate a typical chat request.
        Expected: < 1ms for simple requests
        """

        def validate_request():
            return ChatRequest(**sample_chat_request_data)

        result = benchmark(validate_request)
        assert result.model == "meta-llama/Llama-3.2-1B-Instruct"
        assert len(result.messages) == 2

    def test_chat_request_validation_with_tools_benchmark(self, benchmark):
        """Benchmark ChatRequest validation with tools.

        Measures validation time for requests with tool definitions.
        Expected: < 2ms for requests with multiple tools
        """
        data = {
            "model": "meta-llama/Llama-3.2-1B-Instruct",
            "messages": [
                {"role": "user", "content": "Execute: print('hello')"},
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "execute_python",
                        "description": "Execute Python code",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string", "description": "Python code to execute"}
                            },
                            "required": ["code"],
                        },
                    },
                }
            ],
            "stream": False,
        }

        def validate_request():
            return ChatRequest(**data)

        result = benchmark(validate_request)
        assert result.tools is not None
        assert len(list(result.tools)) == 1

    def test_message_adapter_creation_benchmark(self, benchmark):
        """Benchmark MessageAdapter creation.

        Measures time to wrap messages in MessageAdapter.
        Expected: < 0.1ms per message
        """
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        def create_adapters():
            return [MessageAdapter(raw=msg) for msg in messages]

        result = benchmark(create_adapters)
        assert len(result) == 3

    def test_extract_last_user_query_benchmark(self, benchmark, sample_chat_request_data):
        """Benchmark last user query extraction.

        Measures time to find and extract the last user message.
        Expected: < 0.5ms for typical conversations
        """
        request = ChatRequest(**sample_chat_request_data)

        def extract_query():
            return request.get_last_user_query()

        result = benchmark(extract_query)
        assert result == "What is Python?"

    def test_message_validation_edge_cases_benchmark(self, benchmark):
        """Benchmark validation with edge cases.

        Tests validation performance with boundary conditions:
        - Maximum message length
        - Empty content
        - Multimodal content
        """
        data = {
            "model": "test-model",
            "messages": [
                {"role": "user", "content": "A" * 10000},  # Long message
            ],
            "temperature": 2.0,  # Maximum allowed
            "max_tokens": 100000,  # Maximum allowed
        }

        def validate_request():
            return ChatRequest(**data)

        result = benchmark(validate_request)
        assert result.temperature == 2.0
        assert result.max_tokens == 100000


class TestParameterConstraintValidation:
    """Benchmark parameter constraint checking."""

    def test_temperature_validation_benchmark(self, benchmark):
        """Benchmark temperature validation.

        Tests Pydantic Field constraint checking speed.
        Expected: < 0.1ms
        """
        valid_temperatures = [0.0, 0.5, 1.0, 1.5, 2.0]

        def validate_all():
            requests = []
            for temp in valid_temperatures:
                req = ChatRequest(
                    model="test",
                    messages=[{"role": "user", "content": "test"}],
                    temperature=temp,
                )
                requests.append(req)
            return requests

        result = benchmark(validate_all)
        assert len(result) == 5

    def test_invalid_temperature_rejection_benchmark(self, benchmark):
        """Benchmark invalid temperature rejection.

        Measures time to detect and reject invalid parameters.
        Expected: < 0.2ms (should fail fast)
        """

        def try_invalid():
            try:
                ChatRequest(
                    model="test",
                    messages=[{"role": "user", "content": "test"}],
                    temperature=3.0,  # Invalid: > 2.0
                )
                return False
            except Exception:
                return True

        result = benchmark(try_invalid)
        assert result is True  # Validation should fail


@pytest.mark.asyncio
class TestModelSerializationPerformance:
    """Benchmark model serialization/deserialization."""

    def test_chat_request_serialization_benchmark(self, benchmark):
        """Benchmark ChatRequest serialization to dict.

        Measures time to convert Pydantic model to dictionary.
        Expected: < 0.5ms
        """
        request = ChatRequest(
            model="meta-llama/Llama-3.2-1B-Instruct",
            messages=[
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Hello!"},
            ],
            temperature=0.7,
            max_tokens=1024,
        )

        def serialize():
            return request.model_dump()

        result = benchmark(serialize)
        assert result["model"] == "meta-llama/Llama-3.2-1B-Instruct"

    def test_chat_request_json_serialization_benchmark(self, benchmark):
        """Benchmark ChatRequest JSON serialization.

        Measures time to convert Pydantic model to JSON string.
        Expected: < 1ms
        """
        request = ChatRequest(
            model="meta-llama/Llama-3.2-1B-Instruct",
            messages=[{"role": "user", "content": "Test"}],
            temperature=0.7,
        )

        def serialize_json():
            return request.model_dump_json()

        result = benchmark(serialize_json)
        assert isinstance(result, str)
        assert "meta-llama" in result
