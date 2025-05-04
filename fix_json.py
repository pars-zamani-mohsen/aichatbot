# fix_json.py  

import json  
import os  
import sys  

def fix_json_file(input_file='output.json', output_file='fixed_output.json'):  
    """بررسی و اصلاح فایل JSON نامعتبر"""  
    try:  
        print(f"تلاش برای خواندن فایل JSON از {input_file}...")  
        
        # خواندن کل فایل به صورت متن  
        with open(input_file, 'r', encoding='utf-8') as f:  
            content = f.read()  
        
        # بررسی حجم فایل  
        file_size = os.path.getsize(input_file)  
        print(f"اندازه فایل JSON: {file_size / (1024*1024):.2f} مگابایت")  
        
        # تلاش برای یافتن آخرین براکت معتبر  
        # این روش ساده‌ای برای بررسی و اصلاح فایل JSON است  
        try:  
            # ابتدا سعی کنید کل فایل را پردازش کنید  
            parsed_json = json.loads(content)  
            print("فایل JSON معتبر است!")  
            
            # ذخیره همان فایل با نام جدید  
            with open(output_file, 'w', encoding='utf-8') as f:  
                json.dump(parsed_json, f, ensure_ascii=False, indent=2)  
            
            print(f"فایل JSON بدون تغییر در {output_file} ذخیره شد.")  
            return parsed_json  
            
        except json.JSONDecodeError as e:  
            print(f"خطا در پردازش JSON: {e}")  
            
            # محل خطا را پیدا کنید  
            error_position = e.pos  
            print(f"محل خطا: کاراکتر {error_position}")  
            
            # یافتن آخرین براکت معتبر (یک روش ساده)  
            valid_content = content[:error_position]  
            
            # حدس زدن نوع پرانتز پایانی مورد نیاز  
            if content.strip().startswith('['):  
                valid_content = valid_content.rstrip() + ']'  
            elif content.strip().startswith('{'):  
                valid_content = valid_content.rstrip() + '}'  
            
            # تلاش برای پردازش محتوای اصلاح شده  
            try:  
                fixed_json = json.loads(valid_content)  
                
                # ذخیره فایل اصلاح شده  
                with open(output_file, 'w', encoding='utf-8') as f:  
                    json.dump(fixed_json, f, ensure_ascii=False, indent=2)  
                
                print(f"فایل JSON اصلاح شده در {output_file} ذخیره شد.")  
                return fixed_json  
                
            except json.JSONDecodeError as e2:  
                print(f"خطا در اصلاح خودکار: {e2}")  
                
                # روش دیگر: خواندن خط به خط و تنظیم دستی  
                print("تلاش برای اصلاح با روش خواندن خط به خط...")  
                
                try:  
                    # راه‌حل ساده‌تر: در مورد Scrapy، معمولاً خروجی یک آرایه JSON است  
                    # متن را با براکت شروع و پایان دهید  
                    if not content.strip().startswith('['):  
                        content = '[' + content.strip()  
                    if not content.strip().endswith(']'):  
                        content = content.rstrip() + ']'  
                    
                    # حذف کاماهای اضافی که ممکن است وجود داشته باشد  
                    content = content.replace(',]', ']')  
                    
                    # تلاش مجدد برای تجزیه  
                    fixed_json = json.loads(content)  
                    
                    # ذخیره فایل اصلاح شده  
                    with open(output_file, 'w', encoding='utf-8') as f:  
                        json.dump(fixed_json, f, ensure_ascii=False, indent=2)  
                    
                    print(f"فایل JSON اصلاح شده با روش ساده در {output_file} ذخیره شد.")  
                    return fixed_json  
                    
                except json.JSONDecodeError as e3:  
                    print(f"خطا در اصلاح با روش ساده: {e3}")  
                    
                    # روش نهایی: استخراج اشیاء JSON به صورت تک به تک  
                    print("تلاش برای استخراج اشیاء JSON به صورت تک به تک...")  
                    
                    # این روش برای فایل‌های بزرگ مناسب است  
                    objects = []  
                    bracket_count = 0  
                    current_object = ""  
                    
                    for char in content:  
                        if char == '{':  
                            bracket_count += 1  
                            current_object += char  
                        elif char == '}':  
                            bracket_count -= 1  
                            current_object += char  
                            
                            if bracket_count == 0:  
                                try:  
                                    obj = json.loads(current_object)  
                                    objects.append(obj)  
                                    current_object = ""  
                                except:  
                                    # اگر این شیء معتبر نبود، آن را نادیده بگیرید  
                                    current_object = ""  
                        elif bracket_count > 0:  
                            current_object += char  
                    
                    if objects:  
                        with open(output_file, 'w', encoding='utf-8') as f:  
                            json.dump(objects, f, ensure_ascii=False, indent=2)  
                        
                        print(f"{len(objects)} شیء JSON استخراج و در {output_file} ذخیره شد.")  
                        return objects  
                    else:  
                        print("هیچ شیء JSON معتبری یافت نشد!")  
                        return None  
        
    except Exception as e:  
        print(f"خطای غیرمنتظره: {e}")  
        return None  

if __name__ == "__main__":  
    input_file = 'output.json'  
    if len(sys.argv) > 1:  
        input_file = sys.argv[1]  
    
    output_file = 'fixed_output.json'  
    if len(sys.argv) > 2:  
        output_file = sys.argv[2]  
    
    fix_json_file(input_file, output_file)  
