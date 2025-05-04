# inspect_json.py  

import sys  
import os  

def inspect_json_file(filename='output.json'):  
    """بررسی دقیق محتوای فایل JSON"""  
    try:  
        # بررسی اندازه فایل  
        file_size = os.path.getsize(filename)  
        print(f"اندازه فایل: {file_size / (1024*1024):.2f} مگابایت")  
        
        with open(filename, 'r', encoding='utf-8') as f:  
            content = f.read()  
        
        # بررسی تعداد شیء JSON  
        curly_open = content.count('{')  
        curly_close = content.count('}')  
        
        print(f"تعداد '{{': {curly_open}")  
        print(f"تعداد '}}': {curly_close}")  
        
        # بررسی براکت‌های آرایه  
        square_open = content.count('[')  
        square_close = content.count(']')  
        
        print(f"تعداد '[': {square_open}")  
        print(f"تعداد ']': {square_close}")  
        
        # چک کردن خط پایانی  
        lines = content.split('\n')  
        last_lines = lines[-5:] if len(lines) >= 5 else lines  
        
        print("\nپنج خط آخر فایل:")  
        for i, line in enumerate(last_lines):  
            print(f"{len(lines) - len(last_lines) + i + 1}: {line}")  
        
        # بررسی کاراکتر مورد نظر  
        if len(sys.argv) > 2:  
            position = int(sys.argv[2])  
            context_size = 100  
            start = max(0, position - context_size)  
            end = min(len(content), position + context_size)  
            
            print(f"\nمحتوا در اطراف کاراکتر {position}:")  
            print(f"...{content[start:position]}[HERE]{content[position:end]}...")  
        
    except Exception as e:  
        print(f"خطا در بررسی فایل: {e}")  

if __name__ == "__main__":  
    filename = 'output.json'  
    if len(sys.argv) > 1:  
        filename = sys.argv[1]  
    
    inspect_json_file(filename)  
