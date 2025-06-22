import zipfile
import json
import csv
from io import StringIO
import re

def identify_file_type(filepath):
    with open(filepath, "rb") as f:
        header = f.read(10)

    print("🔹 File Header (first 10 bytes):", header)

    if header.startswith(b'\xff\xd8\xff'):
        print("Identified: .jpg")
        return ".jpg"
    elif header.startswith(b'\x89PNG\r\n\x1a\n'):
        print("Identified: .png")
        return ".png"
    elif header.startswith(b'GIF'):
        print("Identified: .gif")
        return ".gif"
    elif header.startswith(b'%PDF'):
        print("Identified: .pdf")
        return ".pdf"
    elif header.startswith(b'PK'):
        print("📦 ZIP-based format detected. Checking contents...")
        try:
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                names = zip_ref.namelist()
                if any(name.startswith("word/") for name in names):
                    print("Identified: .docx")
                    return ".docx"
                elif any(name.startswith("xl/") for name in names):
                    print("Identified: .xlsx")
                    return ".xlsx"
                elif any(name.startswith("ppt/") for name in names):
                    print("Identified: .pptx")
                    return ".pptx"
                else:
                    print("Identified: .zip")
                    return ".zip"
        except zipfile.BadZipFile:
            print("❌ Corrupted ZIP or not a valid ZIP format.")
            return ".bin"
    else:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                try:
                    json.loads(content)
                    print("Identified: .json")
                    return ".json"
                except json.JSONDecodeError:
                    pass
                if is_likely_csv(content):
                    print("Identified: .csv")
                    return ".csv"
                print("Identified: .txt")
                return ".txt"
                
        except UnicodeDecodeError:
            print("❓ Unknown or binary file (not UTF-8).")
            return ".bin"

def is_likely_csv(content, sample_lines=20):
    """Robust CSV detection with multiple validation layers"""
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if len(lines) < 2:
        return False  
    try:
        sample = '\n'.join(lines[:min(sample_lines, len(lines))])
        dialect = csv.Sniffer().sniff(sample)
        
        reader = csv.reader(StringIO(sample), dialect)
        try:
            header = next(reader)  
            if len(header) < 2:
                return False
        except StopIteration:
            return False
        row_count = 0
        col_counts = set()
        for row in reader:
            if not row:  
                continue
            col_counts.add(len(row))
            row_count += 1
            if row_count >= 5:  
                break

        if row_count >= 1:
            if len(col_counts) == 1:  
                return True
            if max(col_counts) - min(col_counts) <= 1:
                return True
    except Exception:
        pass
    
    delimiters = [',', '\t', ';', '|']
    best_delimiter = None
    best_score = 0
    
    for delimiter in delimiters:
        if content.count(delimiter) < len(lines):
            continue 
       
        scores = []
        for line in lines[:sample_lines]:
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(delimiter) if p.strip()]
            if len(parts) > 1:  
                scores.append(len(parts))
        
        if len(scores) < 2:
            continue
            
        avg_cols = sum(scores) / len(scores)
        consistency = sum(1 for s in scores if abs(s - avg_cols) <= 1) / len(scores)
        score = consistency * avg_cols  
        if score > best_score:
            best_score = score
            best_delimiter = delimiter
    
    if best_delimiter and best_score >= 1.5:
       
        sample_data = lines[1:min(6, len(lines))]  
        if not sample_data:
            return False
            
        valid_lines = 0
        for line in sample_data:
            parts = [p.strip() for p in line.split(best_delimiter) if p.strip()]
            if len(parts) >= 2 and any(len(p) > 3 for p in parts):
                valid_lines += 1
        
        if valid_lines / len(sample_data) >= 0.6: 
            return True
    
    patterns = [
        r'^([^",\r\n]+)(,[^",\r\n]+)+$',  
        r'^([^"\t\r\n]+)(\t[^"\t\r\n]+)+$', 
        r'^([^";\r\n]+)(;[^";\r\n]+)+$', 
        r'^".*?"(?:,".*?")+$',  
        r'^[^,]+,[^,]+,[^,]+$'  
    ]
    
    matching_lines = 0
    tested_lines = lines[:min(sample_lines, len(lines))]
    for line in tested_lines:
        if any(re.match(p, line) for p in patterns):
            matching_lines += 1
  
    if matching_lines / len(tested_lines) > 0.7:
        return True
    
    return False