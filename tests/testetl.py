import re
from typing import List, Dict
from collections import Counter

def clean_text(text: str) -> str:
    """
    Remove non-alphanumeric characters from the input text,
    keeping only letters, numbers, and spaces.
    """
    return re.sub(r'[^a-zA-Z0-9\s]', '', text).lower()

def tokenize(text: str) -> List[str]:
    """
    Tokenize the text by lowercasing and splitting on whitespace.
    """
    return re.findall(r'\b\w+\b', text)

def jaccard_similarity(text1: str, text2: str) -> float:
    """
    Compute the Jaccard similarity between two texts.
    """
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    set1 = set(tokens1)
    set2 = set(tokens2)
    if not set1 and not set2:
        return 1.0  # Both texts are empty
    if not set1 or not set2:
        return 0.0  # One of the texts is empty
    return len(set1 & set2) / len(set1 | set2)

def cosine_similarity(text1: str, text2: str) -> float:
    """
    Compute the cosine similarity between two texts.
    """
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    counter1 = Counter(tokens1)
    counter2 = Counter(tokens2)
    
    intersection = sum((counter1 & counter2).values())
    norm1 = sum(count ** 2 for count in counter1.values()) ** 0.5
    norm2 = sum(count ** 2 for count in counter2.values()) ** 0.5
    
    if norm1 == 0 or norm2 == 0:
        return 0.0  # Prevent division by zero
    
    return intersection / (norm1 * norm2)

def test_etl_pipeline(existing_facts: List[Dict[str, str]], new_data: List[Dict[str, str]], similarity_threshold: float = 0.4):
    """
    Test the ETL pipeline by comparing new data against existing facts.
    
    Args:
        existing_facts (list of dict): Existing facts in the database.
        new_data (list of dict): New data to be processed.
        similarity_threshold (float): The threshold above which facts are considered similar.
    
    Prints the actions that would be taken (e.g., update or insert).
    """
    for new_item in new_data:
        new_fact = clean_text(new_item.get("fact", ""))
        matched = False

        print(f"New Fact: '{new_fact}'")

        for existing_item in existing_facts:
            existing_fact_text = clean_text(existing_item["fact"])
            # Use cosine similarity
            similarity = cosine_similarity(new_fact, existing_fact_text)

            print(f"Comparing with: '{existing_fact_text}'")
            print(f"Similarity: {similarity:.2f}")

            if similarity >= similarity_threshold:
                print(f"Would update: '{existing_fact_text}' to '{new_fact}' (Similarity: {similarity:.2f})")
                matched = True
                break

        if not matched:
            print(f"Would insert new fact: '{new_fact}'")



# Sample existing facts in the database
existing_facts = [
    {"fact": "Dogs have an extraordinary sense of smell."},
    {"fact": "Puppies are born blind, deaf, and toothless."},
    {"fact": "There are more than 340 dog breeds worldwide."},
]

# Sample new data to be processed
new_data = [
    {"fact": "A dog’s sense of smell is at least 40x better than ours."},
    {"fact": "Puppies are born without sight or hearing."},
    {"fact": "Dogs can learn more than 1000 words."},
]

# Run the test with a lower threshold if needed
test_etl_pipeline(existing_facts, new_data, similarity_threshold=0.4)