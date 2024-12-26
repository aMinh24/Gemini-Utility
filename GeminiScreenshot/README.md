# Hướng dẫn cài đặt và sử dụng Gemini Screenshot

## Cài đặt môi trường Python và các thư viện cần thiết

Để sử dụng chương trình Gemini Screenshot, bạn cần cài đặt Python và các thư viện sau:

1.  **Cài đặt Python:**
    *   Tải Python từ trang web chính thức: [https://www.python.org/downloads/](https://www.python.org/downloads/)
    *   Chọn phiên bản Python 3.7 trở lên và cài đặt.
    *   Trong quá trình cài đặt, hãy chắc chắn chọn "Add Python to PATH" để có thể chạy Python từ command line.

2.  **Cài đặt các thư viện cần thiết:**
    *   Mở command line (cmd) hoặc PowerShell.
    *   Chạy lệnh sau để cài đặt các thư viện:
        ```
        pip install Pillow requests cryptography python-dotenv
        ```

## Tạo shortcut cho file `Gemini_Screen.vbs` và gán phím tắt

1.  **Tạo shortcut:**
    *   Tìm file `Gemini_Screen.vbs` trong thư mục.
    *   Click chuột phải vào file, chọn "Create shortcut".
    *   Kéo shortcut vừa tạo ra desktop.

2.  **Gán phím tắt:**
    *   Click chuột phải vào shortcut trên desktop, chọn "Properties".
    *   Chọn tab "Shortcut".
    *   Click vào ô "Shortcut key" và nhấn tổ hợp phím bạn muốn gán (ví dụ: Ctrl + Shift + G).
    *   Nhấn "OK" để lưu lại.

## Hướng dẫn sử dụng

1.  **Chạy chương trình:**
    *   Mở chương trình bằng cách click vào shortcut trên desktop hoặc sử dụng phím tắt đã gán.

2.  **Chụp màn hình và chỉnh sửa:**
    *   Chương trình sẽ tự động chụp toàn bộ màn hình và mở bằng Paint.
    *   Bạn có thể chỉnh sửa ảnh trên Paint.

3.  **Lưu và gửi yêu cầu:**
    *   Sau khi chỉnh sửa, nhấn `Ctrl + S` để lưu ảnh.
    *   Một hộp thoại prompt sẽ hiện ra.
    *   Nhập prompt (câu hỏi hoặc yêu cầu) vào hộp thoại.
    *   Nhấn "OK" để gửi yêu cầu đến Gemini.

4.  **Nhận kết quả:**
    *   Kết quả từ Gemini sẽ được hiển thị trên một trang web mới trên Chrome.

## Cài đặt nâng cao

*   Trong hộp thoại prompt, có nút "Cài đặt" để thay đổi:
    *   **Prompt Templates:** Các template prompt có sẵn để bạn chọn.
    *   **Model:** Chọn model Gemini (chỉ các model thuộc Google).
    *   **Thời gian chờ tối đa:** Thời gian tối đa chương trình chờ phản hồi từ Gemini (tính bằng giây).

**Lưu ý:**
*   Nếu muốn thay đổi API key vui lòng xóa file .env trong cùng thư mục
*   Chương trình sử dụng API key của Gemini. Bạn sẽ được yêu cầu nhập API key khi chạy chương trình lần đầu tiên.
*   File `config.json` chứa các cài đặt của chương trình, bạn có thể chỉnh sửa trực tiếp file này nếu muốn.
