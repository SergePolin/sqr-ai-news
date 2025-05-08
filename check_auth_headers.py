#!/usr/bin/env python3
import os
import re

def find_incorrect_auth_headers(directory):
    """
    Find all incorrect authentication headers in test files.
    
    Look for patterns like:
    - headers={"Authorization": f"***"}
    - headers={"Authorization": token}
    - headers={"Authorization": f"{token}"}
    
    Instead of the correct:
    - headers={"Authorization": f"Bearer {token}"}
    """
    incorrect_headers = []
    
    # Regex patterns to look for
    patterns = [
        r'headers=\{"Authorization":\s*f?"[^B][^e][^a][^r][^e][^r].*?"\}',  # Any Authorization that doesn't start with Bearer
        r'headers=\{"Authorization":\s*f?"{token}"\}',  # Just token without Bearer
        r'headers=\{"Authorization":\s*token\}',  # token without quotes and Bearer
        r'headers=\{"Authorization":\s*"\*\*\*"\}',  # *** placeholder
        r'headers=\{"Authorization":\s*f"\*\*\*"\}',  # f"***" placeholder
    ]
    
    # Walk through the directory looking for Python files
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                line_number = 1
                for line in content.splitlines():
                    for pattern in patterns:
                        if re.search(pattern, line):
                            incorrect_headers.append({
                                'file': file_path,
                                'line': line_number,
                                'content': line.strip()
                            })
                    line_number += 1
    
    return incorrect_headers

if __name__ == "__main__":
    incorrect_headers = find_incorrect_auth_headers('tests')
    if incorrect_headers:
        print(f"Found {len(incorrect_headers)} incorrect authentication headers:")
        for item in incorrect_headers:
            print(f"{item['file']}:{item['line']}: {item['content']}")
    else:
        print("No incorrect authentication headers found.") 