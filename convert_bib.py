# -*- coding: utf-8 -*-
"""
Created on Sat Sep  5 18:10:35 2026

@author: cartin
"""

import os
import re
import json

BIB_FILE = 'publications.bib'
OUTPUT_DIR = '_publications'

os.makedirs(OUTPUT_DIR, exist_ok=True)

MONTH_MAP = {
    'jan': '01', 'january': '01', 'feb': '02', 'february': '02',
    'mar': '03', 'march': '03', 'apr': '04', 'april': '04',
    'may': '05', 'jun': '06', 'june': '06', 'jul': '07', 'july': '07',
    'aug': '08', 'august': '08', 'sep': '09', 'september': '09',
    'oct': '10', 'october': '10', 'nov': '11', 'november': '11',
    'dec': '12', 'december': '12'
}

def clean_latex(text):
    """Strips BibTeX curly braces outside of LaTeX math mode ($...$ or $$...$$)."""
    if not text:
        return ""
    parts = re.split(r'(\$\$.*?\$\$|\$.*?\$)', text)
    cleaned_parts = []
    for part in parts:
        if part.startswith('$') and part.endswith('$'):
            cleaned_parts.append(part)
        else:
            cleaned_parts.append(re.sub(r'[\{\}]', '', part))
    return "".join(cleaned_parts).strip()

def format_authors(author_str):
    """Parses all authors from a BibTeX author string regardless of count."""
    if not author_str:
        return "D. Cartin"
    
    # Clean LaTeX braces outside math mode
    clean_str = clean_latex(author_str).strip('"\'')
    
    # Split strictly on ' and ' (BibTeX author delimiter)
    raw_authors = re.split(r'\s+and\s+', clean_str, flags=re.IGNORECASE)
    
    formatted_authors = []
    for a in raw_authors:
        a = a.strip()
        if not a:
            continue
        
        # Convert "Last, First Middle" -> "First Middle Last"
        if ',' in a:
            parts = [p.strip() for p in a.split(',', 1)]
            a = f"{parts[1]} {parts[0]}"
            
        formatted_authors.append(a)
        
    if not formatted_authors:
        return "D. Cartin"
    elif len(formatted_authors) == 1:
        return formatted_authors[0]
    elif len(formatted_authors) == 2:
        return f"{formatted_authors[0]} and {formatted_authors[1]}"
    else:
        return ", ".join(formatted_authors[:-1]) + f", and {formatted_authors[-1]}"

def parse_bib_blocks(file_path):
    """Parses BibTeX entries robustly, preserving nested braces in field values."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into raw @type{key, entries
    raw_entries = re.split(r'@\w+\s*\{', content)[1:]
    entries = []
    
    field_pattern = re.compile(r'(\w+)\s*=\s*', re.IGNORECASE)
    
    for raw in raw_entries:
        entry = {}
        key_match = re.match(r'^([^,]+),', raw)
        if not key_match:
            continue
        entry['key'] = key_match.group(1).strip()
        
        matches = list(field_pattern.finditer(raw))
        for i, match in enumerate(matches):
            field_name = match.group(1).lower()
            start_val = match.end()
            
            if i + 1 < len(matches):
                val_str = raw[start_val:matches[i+1].start()].rstrip(' \t\n,')
            else:
                val_str = raw[start_val:].rstrip(' \t\n,}')
                
            val_str = val_str.strip()
            # Clean up internal newline whitespace
            val_str = re.sub(r'\s+', ' ', val_str)
            entry[field_name] = val_str
            
        entries.append(entry)
    return entries

entries = parse_bib_blocks(BIB_FILE)

# Clear out previous erroneous markdown files in _publications/
for old_file in os.listdir(OUTPUT_DIR):
    if old_file.endswith('.md'):
        os.remove(os.path.join(OUTPUT_DIR, old_file))
        
for idx, entry in enumerate(entries, 1):
    # Clean latex and strip outer quotes or braces from title
    raw_title = clean_latex(entry.get('title', 'Untitled')).strip('\'"')
    title = raw_title
    
    year = clean_latex(entry.get('year', '2026')).strip('\'"')
    month = MONTH_MAP.get(clean_latex(entry.get('month', '01')).lower().strip('\'"'), '01')
    pub_date = f"{year}-{month}-01"
    
    venue = clean_latex(entry.get('journal', entry.get('booktitle', 'Journal')))
    volume = clean_latex(entry.get('volume', '')).strip('\'"')
    issue = clean_latex(entry.get('number', '')).strip('\'"')
    pages = clean_latex(entry.get('pages', '')).strip('\'"').replace('--', '-')
    
    abstract = clean_latex(entry.get('abstract', ''))
    author = format_authors(entry.get('author', 'D. Cartin'))
    
    # Clean unique slug
    clean_title = re.sub(r'[^a-zA-Z0-9]', '-', title.lower())
    clean_title = re.sub(r'-+', '-', clean_title).strip('-')[:40]
    slug = f"{pub_date}-{clean_title}-{idx}"
    
    filename = f"{slug}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # Build detailed citation string with SINGLE set of quotes around title
    vol_str = f" <b>{volume}</b>" if volume else ""
    issue_str = f"({issue})" if issue else ""
    pages_str = f", {pages}" if pages else ""
    citation_str = f'{author} ({year}). "{title}." <i>{venue}</i>{vol_str}{issue_str}{pages_str}.'

    # Save extra metadata in front matter
    safe_title = json.dumps(title)
    safe_venue = json.dumps(venue)
    safe_citation = json.dumps(citation_str)

    content = f"""---
title: {safe_title}
collection: publications
category: manuscripts
permalink: /publication/{slug}
date: {pub_date}
venue: {safe_venue}
volume: "{volume}"
issue: "{issue}"
pages: "{pages}"
citation: {safe_citation}
---

{abstract}
"""

    with open(filepath, 'w', encoding='utf-8') as out_f:
        out_f.write(content)

print(f"Cleaned folder and generated {len(entries)} publication files with matching permalinks.")