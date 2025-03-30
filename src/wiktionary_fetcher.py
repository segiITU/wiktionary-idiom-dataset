import requests
import csv
import time
import json
import re
import os
from pathlib import Path
from bs4 import BeautifulSoup

def fetch_definition(term):
    """
    Fetch definition for a term using the Wiktionary REST API.
    """
    term = term.strip().lower()
    encoded_term = term.replace(' ', '_')
    
    url = f"https://en.wiktionary.org/api/rest_v1/page/definition/{encoded_term}"
    
    headers = {
        'User-Agent': 'Idiom-Collector/1.0 (your.email@example.com)',
        'Api-User-Agent': 'Idiom-Collector/1.0 (your.email@example.com)'
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'en' in data:
                for part_of_speech in data['en']:
                    for definition in part_of_speech['definitions']:
                        if 'definition' in definition:
                            clean_def = re.sub(r'<[^>]+>', '', definition['definition'])
                            return clean_def
            
            return None
        else:
            print(f"Error: HTTP {response.status_code} for term '{term}'")
            return None
            
    except Exception as e:
        print(f"Exception fetching definition for '{term}': {e}")
        return None

def fetch_definition_via_parse_api(term):
    """
    Alternative method using the MediaWiki Parse API if the REST API fails.
    """
    term = term.strip().lower()
    encoded_term = term.replace(' ', '_')
    
    url = "https://en.wiktionary.org/w/api.php"
    
    params = {
        'action': 'parse',
        'page': encoded_term,
        'format': 'json',
        'prop': 'text',
    }
    
    headers = {
        'User-Agent': 'Idiom-Collector/1.0 (your.email@example.com)'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            
            if 'parse' in data and 'text' in data['parse']:
                html = data['parse']['text']['*']
                
                soup = BeautifulSoup(html, 'html.parser')
                
                definitions = []
                
                english_header = None
                for h2 in soup.find_all('h2'):
                    span = h2.find('span', {'id': 'English'})
                    if span:
                        english_header = h2
                        break
                
                if english_header:
                    current = english_header.next_sibling
                    while current and not (current.name == 'h2' and current.find('span', {'id': lambda x: x and x != 'English'})):
                        if current.name == 'ol':
                            for li in current.find_all('li', recursive=False):
                                definition = li.get_text().strip()
                                definition = re.sub(r'\[\d+\]', '', definition)
                                return definition
                        current = current.next_sibling
                
                for ol in soup.find_all('ol'):
                    for li in ol.find_all('li', recursive=False):
                        definition = li.get_text().strip()
                        definition = re.sub(r'\[\d+\]', '', definition)
                        return definition
            
            return None
        else:
            print(f"Parse API Error: HTTP {response.status_code} for term '{term}'")
            return None
            
    except Exception as e:
        print(f"Exception with Parse API for '{term}': {e}")
        return None

def get_processed_terms(output_file):
    """
    Get the list of terms that have already been processed and saved to the output file.
    This allows resuming from where we left off.
    """
    processed_terms = set()
    try:
        if Path(output_file).exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                next(f, None)  # Skip header
                for line in f:
                    if ',' in line:
                        idiom_part = line.split(',', 1)[0].strip()
                        if idiom_part.startswith('"') and idiom_part.endswith('"'):
                            idiom_part = idiom_part[1:-1].replace('""', '"')
                        processed_terms.add(idiom_part.lower())
    except Exception as e:
        print(f"Warning: Error reading existing output file: {e}")
    
    return processed_terms

def clean_for_csv(text):
    """Prepare a text value for CSV writing - handle quoting and spaces"""
    if text is None:
        return ""
    
    text = text.strip()
    
    if ',' in text or '"' in text:
        text = text.replace('"', '""')
        return f'"{text}"'
    
    return text

def save_term_definition(output_file, term, definition, file_exists=False):
    """
    Save a single term and definition to the CSV file.
    
    Args:
        output_file: Path to the output CSV file
        term: The term/idiom to save
        definition: The definition to save
        file_exists: Whether the file already exists (to determine if header is needed)
    """
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        clean_term = clean_for_csv(term)
        clean_definition = clean_for_csv(definition)
        output_line = f"{clean_term},{clean_definition}\n"
        
        mode = 'a' if file_exists else 'w'
        with open(output_file, mode, encoding='utf-8') as f:
            # Write header if creating a new file
            if not file_exists:
                f.write("idiom,definition\n")
            f.write(output_line)
        
        return True
    except Exception as e:
        print(f"Error saving {term}: {e}")
        return False

def process_terms_one_by_one(input_file, output_file, delay=1.0, start_at=0):
    """
    Process terms one by one, saving after each successful lookup.
    More resilient approach that saves progress immediately.
    
    Args:
        input_file: Path to the input text file with terms
        output_file: Path to the output CSV file
        delay: Delay between API requests in seconds
        start_at: Optional index to start processing from (for resuming)
    """
    file_exists = os.path.exists(output_file)
    
    processed_terms = get_processed_terms(output_file)
    print(f"Found {len(processed_terms)} already processed terms")
    
    all_terms = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                term = line.strip()
                if term:
                    all_terms.append(term)
    except Exception as e:
        print(f"Error reading input file {input_file}: {e}")
        return False
    
    print(f"Loaded {len(all_terms)} terms from {input_file}")
    
    terms_to_process = [term for term in all_terms if term.lower() not in processed_terms]
    print(f"Will process {len(terms_to_process)} remaining terms")
    
    start_idx = max(0, min(start_at, len(terms_to_process) - 1))
    
    success_count = 0
    error_count = 0
    
    for i, term in enumerate(terms_to_process[start_idx:], start_idx):
        print(f"Processing {i+1}/{len(terms_to_process)}: {term}")
        
        if term.lower() in processed_terms:
            print(f"  Already processed, skipping")
            continue
        
        definition = fetch_definition(term)
        
        if not definition:
            print(f"  REST API failed, trying Parse API for '{term}'")
            definition = fetch_definition_via_parse_api(term)
        
        if definition:
            if save_term_definition(output_file, term, definition, file_exists):
                print(f"  Saved definition: {definition[:100]}..." if len(definition) > 100 else f"  Saved definition: {definition}")
                success_count += 1
                file_exists = True  
            else:
                print(f"  Error saving definition for '{term}'")
                error_count += 1
        else:
            print(f"  No definition found for '{term}'")
            error_count += 1
        
        progress = {
            'total_terms': len(all_terms),
            'processed_terms': len(processed_terms) + i + 1 - start_idx,
            'remaining_terms': len(terms_to_process) - (i + 1 - start_idx),
            'success_count': success_count,
            'error_count': error_count,
            'last_processed_term': term,
            'last_processed_index': i,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        progress_file = f"{output_file}.progress.json"
        try:
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save progress file: {e}")
        
        time.sleep(delay)
    
    print(f"\nProcessing complete!")
    print(f"Successfully processed {success_count} terms")
    print(f"Encountered errors for {error_count} terms")
    return True

def main():
    print("Wiktionary Idiom Fetcher")
    print("========================")
    
    # Set up the default paths - using the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__)) or '.'
    default_input = os.path.join(current_dir, "wiktionary.txt")
    default_output = os.path.join(current_dir, "wiktionary.csv")
    
    use_defaults = input(f"Use default paths ({default_input} and {default_output})? (y/n): ").lower()
    
    if use_defaults == 'y':
        input_file = default_input
        output_file = default_output
    else:
        input_file = input("Enter the path to your input text file (one term per line): ")
        output_file = input("Enter the path to your output CSV file: ")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        create_input = input("Would you like to create a sample input file? (y/n): ").lower()
        if create_input == 'y':
            try:
                with open(input_file, 'w', encoding='utf-8') as f:
                    f.write("a chain is only as strong as its weakest link\n")
                    f.write("actions speak louder than words\n")
                    f.write("all cats are grey in the dark\n")
                    f.write("all that glitters is not gold\n")
                    f.write("a penny saved is a penny earned\n")
                print(f"Created sample input file at '{input_file}'")
            except Exception as e:
                print(f"Error creating sample file: {e}")
                return
        else:
            return
    
    progress_file = f"{output_file}.progress.json"
    start_at = 0
    
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                last_index = progress.get('last_processed_index', 0)
                last_term = progress.get('last_processed_term', '')
                
                print(f"\nFound progress file. Last processed term: '{last_term}' (index {last_index})")
                resume = input("Resume from where you left off? (y/n): ").lower()
                
                if resume == 'y':
                    start_at = last_index + 1
                    print(f"Will resume from index {start_at}")
        except Exception as e:
            print(f"Error reading progress file: {e}")
    
    delay = float(input("Delay between requests in seconds (default: 1.0): ") or "1.0")
    
    process_terms_one_by_one(input_file, output_file, delay, start_at)

if __name__ == "__main__":
    main()