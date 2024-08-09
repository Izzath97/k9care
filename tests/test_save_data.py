import pytest
from unittest.mock import MagicMock, patch
from dags.scripts.k9care_etl import save_data


@patch('dags.scripts.k9care_etl.psycopg2.connect')
def test_save_data(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    data = [
        {"fact": "New fact", "category": "number_excluded"},
        {"fact": "Another fact 456", "category": "number_included"}
    ]

    save_data(data, mock_conn)

    curr = mock_conn.cursor()

    curr.execute.assert_any_call("""SELECT fact, category, version
                    FROM facts""")

    curr.execute("""
                INSERT INTO facts (fact, 
                category, version, created_at, updated_at)
                VALUES (%s, %s, 1, NOW(), NOW())
                """, (data[0]['fact'], data[0]['category']))


    curr.execute("""
                        UPDATE facts
                        SET version = %s,
                            updated_at = NOW()
                        WHERE fact = %s
                        """,
                        (2, data[1]['fact']))   

    curr.execute("""
            UPDATE facts
            SET is_deleted = TRUE,
                updated_at = NOW()
            WHERE fact = %s
            """, ('Some fact to delete',)) 

    assert mock_cursor.execute.call_count > 0
    mock_conn.commit.assert_called_once()
    

