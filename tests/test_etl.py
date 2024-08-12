import pytest
import json
import re
from unittest.mock import patch, MagicMock
from collections import Counter
import psycopg2

from etl_script import clean_text, pull_data, filter_data, cosine_similarity, save_data, main_pipeline


def test_clean_text():
    assert clean_text("Hello, World!") == "Hello World"
    assert clean_text("123!@#ABC") == "123ABC"
    assert clean_text("NoSpecial#Characters") == "NoSpecialCharacters"


@patch('etl_script.requests.get')
def test_pull_data_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = json.dumps([{"fact": "Dogs are loyal."}])
    mock_get.return_value = mock_response

    url = "https://example.com/data.json"
    result = pull_data(url)
    assert result == [{"fact": "Dogs are loyal."}]


@patch('etl_script.requests.get')
def test_pull_data_failure(mock_get):
    mock_get.side_effect = Exception("Failed to pull data")
    
    url = "https://example.com/data.json"
    result = pull_data(url)
    assert result is None


def test_filter_data():
    data = [{"fact": "Dogs have 4 legs."}, {"fact": "Cats are agile."}]
    result = filter_data(data)
    assert result == [
        {"fact": "Dogs have 4 legs", "category": "number_included"},
        {"fact": "Cats are agile", "category": "number_excluded"}
    ]


def test_cosine_similarity():
    text1 = "Dogs are friendly"
    text2 = "Dogs are very friendly"
    text3 = "Cats are aloof"

    assert cosine_similarity(text1, text2) > 0.5
    assert cosine_similarity(text1, text3) < 0.5


@patch('etl_script.psycopg2.connect')
def test_save_data(mock_connect):
    mock_conn = mock_connect.return_value
    mock_cursor = mock_conn.cursor.return_value

    data = [
        {"fact": "Dogs are loyal", "category": "number_excluded"},
        {"fact": "Dogs have 4 legs", "category": "number_included"}
    ]

    # Mock existing facts in the database
    mock_cursor.execute.return_value = None
    mock_cursor.fetchall.return_value = [
        ("Dogs are loyal", "number_excluded", 1)
    ]

    save_data(data, mock_conn)

    assert mock_cursor.executemany.called
    assert mock_conn.commit.called
    assert mock_cursor.close.called


@patch('etl_script.save_data')
@patch('etl_script.filter_data')
@patch('etl_script.pull_data')
@patch('etl_script.psycopg2.connect')
def test_main_pipeline(mock_connect, mock_pull_data, mock_filter_data, mock_save_data):
    mock_conn = mock_connect.return_value

    # Mock successful data pull
    mock_pull_data.return_value = [{"fact": "Dogs are loyal."}]
    
    # Mock filtering process
    mock_filter_data.return_value = [{"fact": "Dogs are loyal", "category": "number_excluded"}]

    main_pipeline()

    assert mock_pull_data.called
    assert mock_filter_data.called
    assert mock_save_data.called
    assert mock_conn.close.called


@patch('etl_script.save_data')
@patch('etl_script.filter_data')
@patch('etl_script.pull_data')
@patch('etl_script.psycopg2.connect')
def test_main_pipeline_pull_data_failure(mock_connect, mock_pull_data, mock_filter_data, mock_save_data):
    mock_pull_data.return_value = None

    main_pipeline()

    assert mock_pull_data.called
    assert not mock_filter_data.called
    assert not mock_save_data.called


@patch('etl_script.save_data')
@patch('etl_script.filter_data')
@patch('etl_script.pull_data')
@patch('etl_script.psycopg2.connect')
def test_main_pipeline_filter_data_failure(mock_connect, mock_pull_data, mock_filter_data, mock_save_data):
    mock_pull_data.return_value = [{"fact": "Dogs are loyal."}]
    mock_filter_data.return_value = []

    main_pipeline()

    assert mock_pull_data.called
    assert mock_filter_data.called
    assert not mock_save_data.called

