"""
This file handles the ETL process for K9 care data.
It retrieves data from a remote github source, filters it, 
and then saves it to a PostgreSQL database
"""
import logging
import json
import re
import requests
import psycopg2


def clean_text(text):
    """
    Remove non-alphanumeric characters from the input text,
    keeping only letters, numbers, and spaces.

    Args:
        text (str): The input string to be cleaned.

    Returns:
        str: The cleaned string.
    """
    cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return cleaned_text

def pull_data(url):
    """
    Pulls data from the given URL.

    Args:
        url (str): The URL to pull data from.

    Returns:
        list: A list of JSON objects if successful, None otherwise.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return json.loads(response.text)
    except requests.exceptions.RequestException as e:
        logging.error("Error pulling data from URL: %s", e)
        return None


def filter_data(data):
    """
    Process a list of dictionaries to clean text and categorize based on the presence of numbers.

    Args:
        data (list of dict): List of dictionaries with a 'fact' key.

    Returns:
        list of dict: Processed list with 'fact' and 'category' keys.
    """
    filterd_data = []
    for item in data:
        fact = clean_text(item.get("fact", ""))

        if any(char.isdigit() for char in fact):
            category = "number_included"
        else:
            category = "number_excluded"
        result = {
            "fact": fact,
            "category": category,
        }
        filterd_data.append(result)
    return filterd_data


def save_data(data, conn):
    """
    Save and update data to PostgreSQL database.

    Args:
        data (list of dict): List of dictionaries to be saved.
        conn (psycopg2.connection): PostgreSQL database connection.

    Returns:
        None
    """
    try:
        cur = conn.cursor()
        cur.execute("""SELECT fact, category, version
                    FROM facts""")
        existing_facts = {row[0]: row for row in cur.fetchall()}
        new_fact_set = {item['fact'] for item in data}

        for item in data:
            fact = item['fact']
            category = item['category']
            if fact in existing_facts:
                existing_version = existing_facts[fact][2]
                # Update the new version of the record
                try:
                    cur.execute("""
                        UPDATE facts
                        SET version = %s,
                            updated_at = NOW()
                        WHERE fact = %s
                        """,
                        (existing_version + 1, fact))
                except psycopg2.Error as e:
                    conn.rollback()
                    logging.error("Error occured when updating: %s", e)
                    continue
            else:
                try:
                    cur.execute("""
                        INSERT INTO facts (fact, 
                        category, version, created_at, updated_at)
                        VALUES (%s, %s, 1, NOW(), NOW())
                        """, (fact, category))
                except psycopg2.Error as e:
                    conn.rollback()
                    logging.error("Error occured when inserting: %s", e)
                    continue

        # Soft delete facts that are no longer in the new data
        for existing_fact in existing_facts.keys():
            if existing_fact not in new_fact_set and not \
                existing_facts[existing_fact][3]:
                try:
                    cur.execute("""
                        UPDATE facts
                        SET is_deleted = TRUE,
                            updated_at = NOW()
                        WHERE fact = %s
                        """,
                        (existing_fact,))
                except psycopg2.Error as e:
                    conn.rollback()
                    logging.error("Error occurred when marking as deleted: %s", e)
                    continue
        conn.commit()
        cur.close()
    except psycopg2.Error as e:
        logging.error("Error saving data to DB: %s", e)
        conn.rollback()


def main_pipeline():
    """
    Main ETL pipeline that pulls, transforms, and loads K9 care data.
    """
    url = "https://raw.githubusercontent.com/vetstoria/random-k9-etl/main/source_data.json"
    try:
        data = pull_data(url)
        print("Pulling...")
        if data is None:
            logging.error("Pulling failed!")
            return
        filtered = filter_data(data)
        if not filtered:
            logging.error("Filtering failed!")
            return
        print("Transforming...")
        conn = psycopg2.connect(
            host="postgres",
            database="k9care_db",
            user="postgres",
            password="admin"
        )
        print("Loading...")
        save_data(filtered, conn)
        print("Saving....")
        conn.close()
        print("Finished!")
    except requests.exceptions.RequestException as e:
        logging.error("Request error: %s", e)
    except psycopg2.Error as e:
        logging.error("Database error: %s", e)
    except ValueError as e:
        logging.error("Value error: %s", e)
    except KeyError as e:
        logging.error("Key error: %s", e)

if __name__ == "__main__":
    main_pipeline()
