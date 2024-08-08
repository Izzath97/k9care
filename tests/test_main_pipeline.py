import pytest
from unittest.mock import patch, MagicMock
from dags.scripts.k9care_etl import main_pipeline

@patch('dags.scripts.k9care_etl.pull_data')
@patch('dags.scripts.k9care_etl.filter_data')
@patch('dags.scripts.k9care_etl.save_data')
@patch('dags.scripts.k9care_etl.psycopg2.connect')
def test_main_pipeline(mock_connect, mock_save_data, mock_filter_data, mock_pull_data):
    mock_pull_data.return_value = [{"fact": "Test fact"}]
    mock_filter_data.return_value = [{"fact": "Test fact", "category": "number_excluded"}]
    mock_connect.return_value = MagicMock()

    with patch('builtins.print') as mock_print:
        main_pipeline()
        assert mock_pull_data.called
        assert mock_filter_data.called
        assert mock_save_data.called
        assert mock_print.call_count > 0
