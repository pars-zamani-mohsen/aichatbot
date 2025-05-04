# advanced_json_fix.py
import json

def fix_json(input_path, output_path):
    valid_items = []
    with open(input_path, 'r', encoding='utf-8') as f:
        buffer = ""
        depth = 0
        for line in f:
            buffer += line
            depth += line.count('{') - line.count('}')
            if depth == 0 and buffer.strip():
                try:
                    item = json.loads(buffer)
                    valid_items.append(item)
                    buffer = ""
                except json.JSONDecodeError:
                    buffer = ""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(valid_items, f, indent=2)

fix_json('output.json', 'fixed_output.json')
