import pytest
from dags.scripts.k9care_etl import clean_text

def test_clean_text():
    assert clean_text("Hello, World!") == "Hello World"
    assert clean_text("Test123") == "Test123"
    assert clean_text("Clean this text!@#") == "Clean this text"
    assert clean_text("") == ""
