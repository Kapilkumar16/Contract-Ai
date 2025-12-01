
import pytest
import os

# Set test environment variables
os.environ["AI_PROVIDER"] = "groq"
os.environ["GROQ_API_KEY"] = "test_key_12345"


@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        "api_base_url": "http://localhost:8000",
        "test_pdf_path": "tests/fixtures/sample.pdf"
    }