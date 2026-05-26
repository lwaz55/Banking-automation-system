import os
import re

base_dir = r"c:\Users\wz\Desktop\ai-proj\Sentinels\backend\app"

def replace_prints_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if there's any print(
    if 'print(' not in content:
        return
        
    # Exclude files where print is intended or already handled
    if filepath.endswith("logger.py"):
        return
        
    # We will replace print( with logger.info(
    # Also add import at the top
    
    # Basic regex for replacing print(f"... ") or print("...")
    # Be careful with traceback.print_exc()
    if 'traceback.print_exc()' in content:
        content = content.replace('traceback.print_exc()', 'logger.error("Exception occurred", exc_info=True)')
        
    # Simple replacement for print(
    # We'll use a regex to only match function calls to print, not string contents hopefully
    # But string contents are unlikely to just be print(
    new_content = re.sub(r'(?<!\.)\bprint\(', 'logger.info(', content)
    
    if new_content != content:
        # Add import at the top
        if 'from app.logger import logger' not in new_content:
            new_content = "from app.logger import logger\n" + new_content
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, _, files in os.walk(base_dir):
    for file in files:
        if file.endswith('.py'):
            replace_prints_in_file(os.path.join(root, file))
