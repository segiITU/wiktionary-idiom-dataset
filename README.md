# Wiktionary Idiom Dataset

All credit goes to Wiktionary. This dataset has been extracted, modified and published according Wiktionary's dual-license under the Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0) and the GNU Free Documentation License (GFDL).

### About

This repository contains:
- A cleaned dataset of idioms with definitions extracted from Wiktionary
- Python scripts (in the `src` folder) for fetching and processing the data

### Scripts

The `src` folder includes:
- `wiktionary_fetcher.py`: Fetches idiom definitions from Wiktionary API
- `remove_synonyms_duplicates.py`: Cleans the data by removing duplicates and references

### Usage

Run the scripts in order:

```
python src/wiktionary_fetcher.py
python src/remove_synonyms_duplicates.py
```

### Requirements

- Python 3.6+
- Required packages: requests, beautifulsoup4