import os
import time
import base64
import requests
import io
from PIL import ImageGrab, Image
import tempfile
from tkinter import simpledialog, messagebox
import tkinter as tk
import subprocess
from tkinter import ttk
import re
import webbrowser
import threading
import sys
from cryptography.fernet import Fernet
from dotenv import load_dotenv, find_dotenv, set_key
import json

def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        messagebox.showerror("Lỗi", "Không tìm thấy file config.json.")
        os._exit(1)
    except json.JSONDecodeError:
        messagebox.showerror("Lỗi", "File config.json không hợp lệ.")
        os._exit(1)

config = load_config()
PROMPT_TEMPLATES = config.get("prompt_templates", [])
MODEL = config.get("model", "gemini-2.0-flash-exp")
TIMEOUT = config.get("timeout", 300)

class SettingsDialog(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master=master)
        self.title("Cài đặt")
        self.geometry("600x400")

        # Prompt Templates
        tk.Label(self, text="Prompt Templates (mỗi dòng một template):").pack(pady=5)
        self.prompt_text_area = tk.Text(self, wrap="word", height=5)
        self.prompt_text_area.pack(fill="both", expand=True, padx=10, pady=5)
        self.prompt_text_area.insert("1.0", "\n".join(PROMPT_TEMPLATES))

        # Model
        tk.Label(self, text="Model:").pack(pady=5)
        self.model_entry = tk.Entry(self, width=60)
        self.model_entry.pack(pady=5, padx=10)
        self.model_entry.insert(0, MODEL)

        # Timeout
        tk.Label(self, text="Thời gian chờ (giây):").pack(pady=5)
        self.timeout_entry = tk.Entry(self, width=10)
        self.timeout_entry.pack(pady=5, padx=10)
        self.timeout_entry.insert(0, str(TIMEOUT))

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)
        save_button = tk.Button(button_frame, text="Lưu", command=self.save_settings)
        save_button.pack(side="left", padx=5)
        cancel_button = tk.Button(button_frame, text="Hủy", command=self.cancel)
        cancel_button.pack(side="left", padx=5)

    def save_settings(self):
        global PROMPT_TEMPLATES, MODEL, TIMEOUT
        PROMPT_TEMPLATES = [line.strip() for line in self.prompt_text_area.get("1.0", "end").splitlines() if line.strip()]
        MODEL = self.model_entry.get()
        try:
            TIMEOUT = int(self.timeout_entry.get())
        except ValueError:
            messagebox.showerror("Lỗi", "Thời gian chờ phải là một số nguyên.")
            return
        
        config["prompt_templates"] = PROMPT_TEMPLATES
        config["model"] = MODEL
        config["timeout"] = TIMEOUT
        
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        
        if self.master and hasattr(self.master, 'prompt_combobox'):
            self.master.prompt_combobox['values'] = PROMPT_TEMPLATES
        
        self.destroy()

    def cancel(self):
        self.destroy()

class PromptDialog(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master=master)
        self.title("Nhập Câu Hỏi")
        self.geometry("600x400")
        self.prompt_text = None

        self.prompt_combobox = ttk.Combobox(self, values=PROMPT_TEMPLATES, width=60)
        self.prompt_combobox.pack(pady=10)

        self.text_area = tk.Text(self, wrap="word", height=10)
        self.text_area.pack(fill="both", expand=True)

        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)
        ok_button = tk.Button(button_frame, text="OK", command=self.ok)
        ok_button.pack(side="left", padx=5)
        cancel_button = tk.Button(button_frame, text="Hủy", command=self.cancel)
        cancel_button.pack(side="left", padx=5)
        settings_button = tk.Button(button_frame, text="Cài đặt", command=self.open_settings)
        settings_button.pack(side="left", padx=5)

        self.result = None

    def ok(self):
        if self.prompt_combobox.get():
            self.result = self.prompt_combobox.get() + "\n" + self.text_area.get("1.0", "end-1c")
        else:
            self.result = self.text_area.get("1.0", "end-1c")
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()

    def open_settings(self):
        settings_dialog = SettingsDialog(self)
        self.wait_window(settings_dialog)

    def get_prompt(self):
        self.wait_window(self)
        return self.result

def capture_full_screen_and_edit(root):
    """Chụp toàn bộ màn hình, lưu vào file tạm và mở bằng Paint."""
    screenshot = ImageGrab.grab()
    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    temp_filename = temp_file.name
    screenshot.save(temp_filename)
    temp_file.close()
    log_temp_file(temp_filename, "created")

    try:
        paint_path = os.path.join(os.getenv('WINDIR'), 'system32', 'mspaint.exe')
        process = subprocess.Popen([paint_path, temp_filename])
    except Exception as e:
        print(f"Lỗi mở ảnh bằng Paint: {e}")
        return None

    def check_for_changes(initial_modified_time, process):
        """Kiểm tra sự thay đổi của file ảnh và đóng Paint."""
        try:
            current_modified_time = os.path.getmtime(temp_filename)
            if current_modified_time > initial_modified_time:
                if process.poll() is None:
                    process.terminate()
                root.event_generate("<<FileChanged>>")
                return
        except FileNotFoundError:
            root.event_generate("<<FileChanged>>")
            return
        root.after(100, check_for_changes, initial_modified_time, process)

    initial_modified_time = os.path.getmtime(temp_filename)
    root.after(100, check_for_changes, initial_modified_time, process)
    return temp_filename

def query_gemini_with_image_data(image_path, prompt):
    """Gửi dữ liệu ảnh (từ file) và câu hỏi đến Gemini API."""
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')

    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": "image/png",
                            "data": base64_image
                         }
                    }
                ]
             }
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    result_json = response.json()
    if 'candidates' in result_json and result_json['candidates']:
        return result_json['candidates'][0]['content']['parts'][0]['text']
    else:
        return "Không thể nhận phản hồi từ Gemini."

def show_result_in_browser(result, image_path):
    """Lưu kết quả vào file HTML tạm và mở bằng trình duyệt mặc định."""
    html_content = result
    temp_html_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode='w', encoding='utf-8')
    temp_html_filename = temp_html_file.name
    temp_html_file.write(html_content)
    temp_html_file.close()
    webbrowser.open_new_tab(f"file://{temp_html_filename}")

    try:
        os.remove(image_path)
        log_temp_file(image_path, "deleted")
    except Exception as e:
        print(f"Không thể xóa file ảnh tạm: {e}")
        log_temp_file(image_path, "delete_failed")

    time.sleep(5)
    try:
        os.remove(temp_html_filename)
        log_temp_file(temp_html_filename, "deleted")
    except Exception as e:
        print(f"Không thể xóa file HTML tạm: {e}")
        log_temp_file(temp_html_filename, "delete_failed")

TEMP_FILE_LOG = "temp_files.log"

def cleanup_temp_files():
    """Xóa các file tạm còn sót lại từ lần chạy trước."""
    if os.path.exists(TEMP_FILE_LOG):
        try:
            with open(TEMP_FILE_LOG, "r") as f:
                log_data = json.load(f)
            for file_path, status in log_data.items():
                if status == "created":
                    try:
                        os.remove(file_path)
                        print(f"Đã xóa file tạm còn sót lại: {file_path}")
                    except Exception as e:
                        print(f"Lỗi khi xóa file tạm còn sót lại: {e}")
            os.remove(TEMP_FILE_LOG)
        except Exception as e:
            print(f"Lỗi khi đọc hoặc xóa file log: {e}")

def log_temp_file(file_path, status):
    """Ghi log trạng thái của file tạm."""
    log_data = {}
    if os.path.exists(TEMP_FILE_LOG):
        try:
             with open(TEMP_FILE_LOG, "r") as f:
                log_data = json.load(f)
        except:
            pass
    log_data[file_path] = status
    with open(TEMP_FILE_LOG, "w") as f:
        json.dump(log_data, f)

def timeout_handler(image_path_container, temp_html_filename=None):
    """Xử lý khi chương trình chạy quá thời gian."""
    print("Chương trình đã chạy quá thời gian quy định.")

    # Xóa file ảnh tạm
    if image_path_container[0]:
        try:
            os.remove(image_path_container[0])
            print(f"Đã xóa file ảnh tạm: {image_path_container[0]}")
            log_temp_file(image_path_container[0], "timeout")
        except Exception as e:
            print(f"Lỗi khi xóa file ảnh tạm: {e}")

    # Xóa file HTML tạm (nếu có)
    if temp_html_filename:
        try:
            os.remove(temp_html_filename)
            print(f"Đã xóa file HTML tạm: {temp_html_filename}")
            log_temp_file(temp_html_filename, "timeout")
        except Exception as e:
            print(f"Lỗi khi xóa file HTML tạm: {e}")

    os._exit(1)

def main():
    """Thực hiện quy trình chụp, chỉnh sửa và hỏi Gemini."""
    image_path_container = [None]
    temp_html_filename_container = [None]

    # Hẹn giờ
    timer = threading.Timer(TIMEOUT, timeout_handler, args=(image_path_container, temp_html_filename_container))
    timer.start()

    def on_file_changed():
        """Xử lý sự kiện khi file ảnh thay đổi."""
        image_path = image_path_container[0]
        if image_path:
            prompt_dialog = PromptDialog(root)
            prompt = "Hãy trả lời bằng tiếng việt dưới dạng HTML nền hơi tối dễ nhìn đẹp mắt yêu cầu sau: " + prompt_dialog.get_prompt()
            if prompt:
                # Hiển thị hộp thoại "Đang xử lý"
                processing_dialog = tk.Toplevel(root)
                processing_dialog.title("Đang xử lý")
                tk.Label(processing_dialog, text="Đang xử lý, vui lòng chờ...").pack(padx=20, pady=20)
                processing_dialog.update()

                try:
                    result = query_gemini_with_image_data(image_path, prompt)
                    temp_html_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode='w', encoding='utf-8')
                    temp_html_filename = temp_html_file.name
                    temp_html_filename_container[0]=temp_html_filename
                    temp_html_file.write(result)
                    temp_html_file.close()
                    webbrowser.open_new_tab(f"file://{temp_html_filename}")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
                finally:
                    processing_dialog.destroy()
                    timer.cancel()
        root.quit()

    try:
        root.bind("<<FileChanged>>", lambda event: on_file_changed())
        image_path_container[0] = capture_full_screen_and_edit(root)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
        timer.cancel()
        root.quit()

import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv, find_dotenv, set_key, get_key

def get_api_key():
    """Yêu cầu và lưu trữ API key."""
    load_dotenv(find_dotenv())
    api_key = get_key(".env", "GEMINI_API_KEY")
    if api_key:
        return api_key

    while True:
        api_key = simpledialog.askstring("API Key", "Vui lòng nhập API key của bạn:")
        if api_key:
            with open(".env", "a") as fenv:
                fenv.write(f"GEMINI_API_KEY={api_key}\n")
            break
        else:
            messagebox.showerror("Lỗi", "API key không được để trống.")
    return api_key

if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
    cleanup_temp_files()
    try:
        api_key = get_api_key()
        if api_key:
            try:
                api_key = base64.b64decode(api_key).decode('utf-8')
            except:
                pass
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={api_key}"
        
        image_path_container = [None]
        temp_html_filename_container = [None]

        # Hẹn giờ 60 giây
        timer = threading.Timer(60.0, timeout_handler, args=(image_path_container, temp_html_filename_container))
        timer.start()
        
        def open_settings():
            settings_dialog = SettingsDialog(root)
            root.wait_window(settings_dialog)

        def on_file_changed():
            """Xử lý sự kiện khi file ảnh thay đổi."""
            image_path = image_path_container[0]
            if image_path:
                prompt_dialog = PromptDialog(root)
                prompt = "Hãy trả lời bằng tiếng việt dưới dạng HTML nền hơi tối dễ nhìn đẹp mắt yêu cầu sau: " + prompt_dialog.get_prompt()
                if prompt:
                    # Hiển thị hộp thoại "Đang xử lý"
                    processing_dialog = tk.Toplevel(root)
                    processing_dialog.title("Đang xử lý")
                    tk.Label(processing_dialog, text="Đang xử lý, vui lòng chờ...").pack(padx=20, pady=20)
                    processing_dialog.update()

                    try:
                        result = query_gemini_with_image_data(image_path, prompt)
                        temp_html_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode='w', encoding='utf-8')
                        temp_html_filename = temp_html_file.name
                        temp_html_filename_container[0]=temp_html_filename
                        temp_html_file.write(result)
                        temp_html_file.close()
                        webbrowser.open_new_tab(f"file://{temp_html_filename}")
                    except Exception as e:
                        messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
                    finally:
                        processing_dialog.destroy()
                        timer.cancel()
            root.quit()

        try:
            root.bind("<<FileChanged>>", lambda event: on_file_changed())
            image_path_container[0] = capture_full_screen_and_edit(root)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            timer.cancel()
            root.quit()
        # Settings button
        settings_button = tk.Button(root, text="Cài đặt", command=open_settings)
        settings_button.pack(pady=10)

        root.mainloop()
    except Exception as e:
        messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
        os._exit(1)
