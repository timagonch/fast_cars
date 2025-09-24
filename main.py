# uv init
# uv add openai requests beautifulsoup4
# uv run main.py

import openai 
from openai import OpenAI
import os
import json
import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path

endpoint = "https://cdong1--azure-proxy-web-app.modal.run"
api_key = "supersecretkey"
deployment_name = "gpt-4o"
client = OpenAI(
    base_url=endpoint,
    api_key=api_key
)

# Scrape the website and extract clean text
try:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    response_web = requests.get(
        "https://www.dubizzle.com/blog/cars/timeline-worlds-fastest-cars/",
        headers=headers,
        timeout=30
    )
    print(response_web.status_code, len(response_web.text))
    open("page.html", "wb").write(response_web.content)
    response_web.raise_for_status()  # Raise an exception for bad status codes
    
    # Parse HTML and extract text content
    soup = BeautifulSoup(response_web.content, 'html.parser')
    fastest_cars_text = soup.get_text(separator=' ', strip=True)
    
    print(f"Successfully scraped {len(fastest_cars_text)} characters from the website")
    
except requests.RequestException as e:
    print(f"Error scraping website: {e}")
    exit(1)

response = client.chat.completions.create(
    model=deployment_name,
    messages=[
        {
            "role": "system",
            "content": """You are an expert data scientist with 10+ years of experience in data cleaning, analysis, and preprocessing. Your primary goal is to go over text provided by scraping a website and extract relevant information for analysis.

STRICT RULES AND GUIDELINES:

1. These are the columns you MUST extract for each car:
   - Year (integer)
   - Make and model (string)
   - Horsepower (integer, if available)
   - Top speed (km/h) (integer)
   - Engine displacement (L) (float, if available)
   - Engine type (string, if available), example: "V8", "Electric", "Hybrid", "Inline-4", etc.

2. OUTPUT FORMAT REQUIREMENTS:
   - Return ONLY a valid JSON array
   - Each object represents one car
   - Use null for missing values
   - Ensure all numeric values are properly formatted
   - Do not include any explanatory text, only the JSON

3. DATA EXTRACTION RULES:
   - Convert all speeds to km/h if given in mph (multiply by 1.609)
   - Extract year as a 4-digit number
   - Combine make and model into one field
   - Be precise with horsepower and displacement values
   - if data is missing or ambiguous, use null"""
        },
        {
            "role": "user",
            "content": f"Here is text from scraping a website about fastest cars. Extract the relevant information into a JSON array following the specified format:\n\n{fastest_cars_text}"
        }
    ]
)

# --- Helpers to ensure we always write a JSON file ---
def extract_json_array(text: str) -> str:
    """
    Try to pull the first JSON array from the text (handles code fences or extra text).
    Falls back to the original text stripped.
    """
    if not text:
        return "[]"
    # Strip Markdown code fences if present
    fenced = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.S | re.I)
    if fenced:
        return fenced.group(1).strip()
    # Otherwise, grab the first [...] block
    bracketed = re.search(r"\[.*\]", text, re.S)
    if bracketed:
        return bracketed.group(0).strip()
    return text.strip()  # may still be valid JSON

# Get the response and parse JSON
cwd = Path.cwd()
output_file = cwd / "fastest_cars_data.json"
raw_file = cwd / "fastest_cars_response.txt"

try:
    cars_json_string = response.choices[0].message.content or ""
    print("ChatGPT Response:")
    print(cars_json_string)
    print("\n" + "="*50 + "\n")

    # Save raw response for inspection (always)
    raw_file.write_text(cars_json_string, encoding="utf-8")
    print(f"Saved raw model output to: {raw_file.resolve()}")

    # Extract a clean JSON array and parse
    cleaned = extract_json_array(cars_json_string)
    cars_data = json.loads(cleaned)  # may raise JSONDecodeError

    # Save to JSON file (always reaches here if parsing succeeded)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cars_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully extracted {len(cars_data)} cars and saved to {output_file.resolve()}")
    
    # Display a preview of the data
    print("\nPreview of extracted data:")
    for i, car in enumerate(cars_data[:3]):  # Show first 3 cars
        print(f"{i+1}. {car}")

except json.JSONDecodeError as e:
    # If parsing fails, still write an empty JSON array so the file exists
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("[]")
    print(f"Error parsing JSON response: {e}")
    print(f"Wrote empty JSON array to: {output_file.resolve()}")
    print("Raw response was saved here:")
    print(raw_file.resolve())

except Exception as e:
    # On any other error, also ensure the JSON file exists (empty)
    if not output_file.exists():
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("[]")
    print(f"Error processing response: {e}")
    print(f"(Empty) JSON file location: {output_file.resolve()}")

print(response.choices[0].message.content)
