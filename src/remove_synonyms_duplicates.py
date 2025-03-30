import csv
import os
from pathlib import Path

def comprehensive_clean(input_file, output_file=None):
    """
    Performs comprehensive cleaning on a CSV file:
    1. Removes entries with reference patterns (Synonym of, Alternative form, etc.)
    2. Removes duplicate entries (case-insensitive)
    3. Normalizes formatting
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output file (if None, creates a new file with '_final' suffix)
    """
    if output_file is None:
        input_path = Path(input_file)
        output_file = str(input_path.parent / f"{input_path.stem}_final{input_path.suffix}")
    
    try:
        filter_patterns = [
            "Synonym of",
            "Alternative form",
            "Alternative spelling",
            "Alternative term",
            "Another form of",
            "Another term for",
            "See also"
        ]
        
        rows = []
        filtered_count = 0
        duplicate_count = 0
        total_count = 0
        seen_idioms_lower = set()  
        
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            rows.append(header)
            
            for row in reader:
                total_count += 1
                
                if not row or len(row) < 2:
                    continue
                
                idiom = row[0].strip()
                definition = row[1].strip()
                
                if not idiom:
                    continue
                
                should_filter = any(pattern in definition for pattern in filter_patterns)
                
                if should_filter:
                    filtered_count += 1
                    print(f"Filtering: {idiom} - {definition[:50]}..." if len(definition) > 50 else f"Filtering: {idiom} - {definition}")
                    continue
                
                idiom_lower = idiom.lower()
                if idiom_lower in seen_idioms_lower:
                    duplicate_count += 1
                    print(f"Removing duplicate: {idiom}")
                    continue
                
                seen_idioms_lower.add(idiom_lower)
                
                clean_row = [idiom, definition]
                rows.append(clean_row)
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerows(rows)
        
        print(f"\nComprehensive cleaning complete!")
        print(f"Total entries: {total_count}")
        print(f"Filtered entries: {filtered_count}")
        print(f"Duplicate entries: {duplicate_count}")
        print(f"Final unique entries: {total_count - filtered_count - duplicate_count}")
        print(f"Cleaned data saved to: {output_file}")
        
        return True
    
    except Exception as e:
        print(f"Error processing CSV: {e}")
        return False

def prioritize_cleaned_file(base_file):
    """
    Checks for and prioritizes using the cleaned version of the file if it exists.
    
    Args:
        base_file: The base file path to check for cleaner versions
    
    Returns:
        The path to use as input
    """
    input_path = Path(base_file)
    priority_files = [
        str(input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}"),
        str(input_path.parent / f"{input_path.stem}_unique{input_path.suffix}")
    ]
    
    available_files = [f for f in priority_files if os.path.exists(f)]
    
    if available_files:
        print("Found processed versions of the file:")
        for i, file in enumerate(available_files):
            print(f"{i+1}. {file}")
        print(f"{len(available_files)+1}. Use original file: {base_file}")
        
        choice = input(f"Which file would you like to use as input? (1-{len(available_files)+1}): ")
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(available_files):
                return available_files[choice_idx]
            else:
                return base_file
        except ValueError:
            print("Invalid choice, using original file.")
            return base_file
    
    return base_file

def main():
    print("Idiom CSV Cleaner")
    print("================")
    
    current_dir = os.path.dirname(os.path.abspath(__file__)) or '.'
    default_file = os.path.join(current_dir, "wiktionary.csv")
    
    use_default = input(f"Use default path ({default_file})? (y/n): ").lower()
    
    if use_default == 'y':
        base_file = default_file
    else:
        base_file = input("Enter the path to your CSV file: ")
    
    if not os.path.exists(base_file):
        print(f"Error: File '{base_file}' not found.")
        return
    
    input_file = prioritize_cleaned_file(base_file)
    print(f"Using {input_file} as input")
    
    output_choice = input("Enter the path for output file (or press Enter to auto-generate): ")
    output_file = output_choice if output_choice else None
    
    comprehensive_clean(input_file, output_file)

if __name__ == "__main__":
    main()