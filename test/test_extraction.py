import pytest
from app.services.extraction_service import ExtractionService
from app.models import ExtractedFields

@pytest.fixture
def extraction_service():
    """Fixture for extraction service"""
    return ExtractionService()

def test_extraction_basic_nda(extraction_service):
    """Test extraction from a basic NDA"""
    sample_text = """
    NON-DISCLOSURE AGREEMENT
    
    This Agreement is entered into as of January 15, 2024 (the "Effective Date")
    by and between Acme Corporation ("Disclosing Party") and Tech Solutions Inc ("Receiving Party").
    
    1. Term: This Agreement shall remain in effect for a period of two (2) years from the Effective Date.
    
    2. Governing Law: This Agreement shall be governed by the laws of the State of California.
    
    3. Liability: In no event shall either party's liability exceed $100,000 USD.
    
    Signed:
    John Smith, CEO, Acme Corporation
    Jane Doe, CTO, Tech Solutions Inc
    """
    
    result = extraction_service.extract_fields(sample_text)
    
    assert isinstance(result, ExtractedFields)
    assert len(result.parties) >= 1
    assert result.effective_date is not None
    assert "California" in (result.governing_law or "")

def test_extraction_handles_missing_fields(extraction_service):
    """Test that extraction handles documents with missing fields gracefully"""
    minimal_text = """
    Simple agreement between Party A and Party B.
    """
    
    result = extraction_service.extract_fields(minimal_text)
    
   
    assert isinstance(result, ExtractedFields)
    
    assert isinstance(result.parties, list)

def test_extraction_empty_document(extraction_service):
    """Edge case: empty document"""
    result = extraction_service.extract_fields("")
    
    assert isinstance(result, ExtractedFields)
    assert len(result.parties) == 0

def test_extraction_very_long_document(extraction_service):
    """Test extraction handles long documents (truncation)"""
    long_text = "Lorem ipsum dolor sit amet. " * 1000  
    
    result = extraction_service.extract_fields(long_text)
    
 
    assert isinstance(result, ExtractedFields)

@pytest.mark.parametrize("date_format,expected_year", [
    ("01/15/2024", "2024"),
    ("2024-01-15", "2024"),
    ("January 15, 2024", "2024"),
])
def test_extraction_date_formats(extraction_service, date_format, expected_year):
    """Test extraction handles various date formats"""
    text = f"""
    Agreement dated {date_format}
    Between Party A and Party B
    """
    
    result = extraction_service.extract_fields(text)
    
   
    assert isinstance(result, ExtractedFields)