import pytest
import responses
from dags.scripts.k9care_etl import pull_data

@responses.activate
def test_pull_data():
    url = "https://raw.githubusercontent.com/vetstoria/random-k9-etl/main/source_data.json"
    mock_data = [{"fact": "This is a fact 1"}, {"fact": "Another fact 2"}]
    responses.add(responses.GET, url, json=mock_data, status=200)

    result = pull_data(url)
    assert result == mock_data

@responses.activate
def test_pull_data_failure():
    url = "https://raw.githubusercontent.com/vetstoria/random-k9-etl/main/source_data.json"
    responses.add(responses.GET, url, body="Error", status=500)

    result = pull_data(url)
    assert result is None
