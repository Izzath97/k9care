"""
This file handles the ETL process for K9 care data.
It retrieves data from a remote GitHub source, filters it,
and then saves it to a PostgreSQL database.
"""
import logging
import json
import re
from collections import Counter
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
    filtered_data = []
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
        filtered_data.append(result)
    return filtered_data


def cosine_similarity(text1, text2):
    """
    Compute the cosine similarity between two pieces of text.

    Args:
        text1 (str): First piece of text.
        text2 (str): Second piece of text.

    Returns:
        float: Cosine similarity score.
    """
    counter1 = Counter(text1.split())
    counter2 = Counter(text2.split())

    intersection = sum((counter1 & counter2).values())
    norm1 = sum(value ** 2 for value in counter1.values()) ** 0.5
    norm2 = sum(value ** 2 for value in counter2.values()) ** 0.5

    if not norm1 or not norm2:
        return 0.0

    return intersection / (norm1 * norm2)


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
        cur.execute("SELECT fact, category, version FROM facts WHERE is_deleted = FALSE")
        existing_facts = {row[0]: row for row in cur.fetchall()}
        new_fact_set = {item['fact'] for item in data}

        # Lists to store records to update or insert
        update_records = []
        insert_records = []

        for item in data:
            new_fact = item['fact']
            category = item['category']
            updated = False

            for existing_fact_text, existing_fact_data in existing_facts.items():
                similarity = cosine_similarity(new_fact, existing_fact_text)
                if similarity >= 0.4:
                    print(f"Would update: '{existing_fact_text}' to '\
                        {new_fact}'(Similarity: {similarity:.2f})")
                    update_records.append((new_fact, category,
                                        existing_fact_data[2] + 1, existing_fact_text))
                    updated = True
                    break

            if not updated:
                print(f"Would insert new fact: '{new_fact}'")
                insert_records.append((new_fact, category))

        # Perform bulk updates
        if update_records:
            cur.executemany("""
                UPDATE facts
                SET fact = %s, category = %s, version = %s, updated_at = NOW()
                WHERE fact = %s
            """, update_records)

        # Perform bulk inserts
        if insert_records:
            cur.executemany("""
                INSERT INTO facts (fact, category, version, created_at, updated_at)
                VALUES (%s, %s, 1, NOW(), NOW())
            """, insert_records)

        # Soft delete facts that are no longer in the new data
        for existing_fact in existing_facts.keys():
            if existing_fact not in new_fact_set:
                cur.execute("""
                    UPDATE facts
                    SET is_deleted = TRUE, updated_at = NOW()
                    WHERE fact = %s
                """, (existing_fact,))
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
