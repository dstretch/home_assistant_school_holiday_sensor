#!/usr/bin/env python3
"""
Validation script for holiday and translation files.
Can be run locally to validate files before committing.
"""

import json
import yaml
import sys
import glob
import argparse
from datetime import datetime
from collections import defaultdict
from pathlib import Path

def parse_date(value):
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: {value}")


def validate_date_format(date_str):
    """Validate provided date format"""
    try:
        parse_date(date_str)
        return True
    except ValueError:
        return False


def validate_holiday_file(filepath):
    """Validate a single holiday YAML file"""
    print(f"Validating {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if not isinstance(data, list):
        raise ValueError('Root element must be a list')
    
    for region in data:
        if not isinstance(region, dict):
            raise ValueError('Each region must be a dictionary')
        
        if 'name' not in region:
            raise ValueError('Each region must have a name')
        
        if 'holidays' not in region:
            raise ValueError('Each region must have holidays')
        
        if not isinstance(region['holidays'], list):
            raise ValueError('Holidays must be a list')
        
        for holiday in region['holidays']:
            if not isinstance(holiday, dict):
                raise ValueError('Each holiday must be a dictionary')
            
            required_fields = ['name', 'date_from', 'date_till']
            for field in required_fields:
                if field not in holiday:
                    raise ValueError(f'Holiday missing required field: {field}')
            
            if not validate_date_format(holiday['date_from']):
                raise ValueError(f'Invalid date_from format: {holiday["date_from"]} (expected YYYY-MM-DD or DD-MM-YYYY)')
            
            if not validate_date_format(holiday['date_till']):
                raise ValueError(f'Invalid date_till format: {holiday["date_till"]} (expected YYYY-MM-DD or DD-MM-YYYY)')
            
            # Validate date logic
            from_date = parse_date(holiday['date_from'])
            till_date = parse_date(holiday['date_till'])
            
            if from_date > till_date:
                raise ValueError(f'date_from ({holiday["date_from"]}) cannot be after date_till ({holiday["date_till"]})')
            
            # Check for year consistency in holiday name vs dates
            holiday_name = holiday['name'].lower()
            from_year = from_date.year
            till_year = till_date.year
            
            # Extract year from holiday name if present
            import re
            name_years = re.findall(r'20\d{2}', holiday_name)
            if name_years:
                name_year = int(name_years[0])
                if name_year != from_year and name_year != till_year:
                    raise ValueError(f'Holiday name year ({name_year}) does not match date years ({from_year}-{till_year})')
    
    print(f"✓ {filepath} - Valid")
    return True


def get_nested_keys(data, prefix=''):
    """Recursively get all nested keys"""
    keys = set()
    if isinstance(data, dict):
        for key, value in data.items():
            current_key = f'{prefix}.{key}' if prefix else key
            keys.add(current_key)
            if isinstance(value, dict):
                keys.update(get_nested_keys(value, current_key))
    return keys


def validate_translation_file(filepath):
    """Validate a single translation JSON file"""
    print(f"Validating {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Check for duplicate keys
    def check_duplicates(data, path=''):
        if isinstance(data, dict):
            seen_keys = set()
            for key, value in data.items():
                if key in seen_keys:
                    raise ValueError(f'Duplicate key "{key}" found at path "{path}"')
                seen_keys.add(key)
                check_duplicates(value, f'{path}.{key}' if path else key)
    
    check_duplicates(data)
    
    # Validate required structure
    required_structure = {
        'config.step.user.title',
        'config.step.region.title', 
        'config.step.holidays.title',
        'config.abort.already_configured'
    }
    
    file_keys = get_nested_keys(data)
    missing_required = required_structure - file_keys
    if missing_required:
        raise ValueError(f'Missing required keys: {missing_required}')
    
    print(f"✓ {filepath} - Valid")
    return True


def validate_all_translations_consistent():
    """Validate that all translation files have consistent keys"""
    print("Validating translation file consistency...")
    
    translation_files = glob.glob('custom_components/school_holiday_sensor/translations/*.json')
    translations = {}
    
    for file in translation_files:
        with open(file, 'r', encoding='utf-8') as f:
            translations[file] = json.load(f)
    
    # Get all keys from all files
    all_keys = set()
    for file, data in translations.items():
        keys = get_nested_keys(data)
        all_keys.update(keys)
    
    # Check if all files have the same keys
    missing_keys = defaultdict(list)
    for file, data in translations.items():
        file_keys = get_nested_keys(data)
        for key in all_keys:
            if key not in file_keys:
                missing_keys[key].append(file)
    
    if missing_keys:
        print('✗ Translation files have missing keys:')
        for key, files in missing_keys.items():
            print(f'  Key "{key}" missing in: {", ".join(files)}')
        return False
    
    print("✓ All translation files have consistent structure!")
    return True


def main():
    parser = argparse.ArgumentParser(description='Validate holiday and translation files')
    parser.add_argument('--holidays', action='store_true', help='Validate only holiday files')
    parser.add_argument('--translations', action='store_true', help='Validate only translation files')
    parser.add_argument('--file', type=str, help='Validate specific file')
    
    args = parser.parse_args()
    
    # Change to script directory
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)
    
    errors = []
    
    if args.file:
        # Validate specific file
        if args.file.endswith('.yaml'):
            try:
                validate_holiday_file(args.file)
            except Exception as e:
                print(f"✗ {args.file} - {e}")
                errors.append(f"{args.file}: {e}")
        elif args.file.endswith('.json'):
            try:
                validate_translation_file(args.file)
            except Exception as e:
                print(f"✗ {args.file} - {e}")
                errors.append(f"{args.file}: {e}")
        else:
            print(f"Unknown file type: {args.file}")
            sys.exit(1)
    else:
        # Validate all files
        if not args.translations:
            # Validate holiday files
            print("=== Validating Holiday Files ===")
            holiday_files = glob.glob('custom_components/school_holiday_sensor/holidays/*.yaml')
            for file in holiday_files:
                try:
                    validate_holiday_file(file)
                except Exception as e:
                    print(f"✗ {file} - {e}")
                    errors.append(f"{file}: {e}")
        
        if not args.holidays:
            # Validate translation files
            print("\n=== Validating Translation Files ===")
            translation_files = glob.glob('custom_components/school_holiday_sensor/translations/*.json')
            for file in translation_files:
                try:
                    validate_translation_file(file)
                except Exception as e:
                    print(f"✗ {file} - {e}")
                    errors.append(f"{file}: {e}")
            
            # Validate consistency
            print("\n=== Validating Translation Consistency ===")
            if not validate_all_translations_consistent():
                errors.append("Translation files are not consistent")
    
    if errors:
        print(f"\n✗ Validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("\n✓ All validations passed!")


if __name__ == '__main__':
    import os
    main()
