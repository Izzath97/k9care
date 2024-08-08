import pytest
from dags.scripts.k9care_etl import filter_data

def test_filter_data():
    input_data = [{"fact": "This fact 123"}, {"fact": "No numbers here"}]
    expected_output = [
        {"fact": "This fact 123", "category": "number_included"},
        {"fact": "No numbers here", "category": "number_excluded"}
    ]
    assert filter_data(input_data) == expected_output
