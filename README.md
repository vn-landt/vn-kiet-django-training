# 🚀 Img2XL Django App

Ứng dụng Django hỗ trợ xử lý hình ảnh (Img2XL), deploy trên Google App Engine.

---

## 📦 Yêu cầu hệ thống

* Python 2.7 ⚠️ (bắt buộc do App Engine legacy)
* pip
* virtualenv (khuyến khích)

---

## 📥 Clone project

Clone đúng nhánh `img2xl_app`:

```bash
git clone -b img2xl_app https://github.com/vn-landt/vn-kiet-django-training.git
cd vn-kiet-django-training
```

---

## Tạo môi trường ảo

```bash
python -m virtualenv venv
```

Kích hoạt môi trường:

**Windows**

```bash
venv\Scripts\activate
```

**Linux / MacOS**

```bash
source venv/bin/activate
```

---

## 📚 Cài đặt thư viện cần thiết

```bash
pip install -r requirements.txt
```

---

## ⚙️ Cấu hình `app.yaml`

### Bước 1: Tạo file

```bash
cp app.yaml.example app.yaml
```

**Windows:**

```bash
copy app.yaml.example app.yaml
```

---

### Bước 2: Cập nhật nội dung

Mở file `app.yaml` và chỉnh sửa:

```yaml

env_variables:
  DJANGO_SETTINGS_MODULE: "img2xl_project.settings"
  GEMINI_API_KEY: "YOUR_GEMINI_API"
  IMGBB_API_KEY: "YOUR_IMGBB_API"
  # Thêm cấu hình Email vào đây
  EMAIL_USER: "your-email@gmail.com"
  EMAIL_PASS: "abcd efgh ijkl mnop" # 16 ký tự mật khẩu ứng dụng


```

---

### 🔑 Giải thích biến môi trường

| Biến                     | Mô tả                              | Lấy từ                                  |
| ------------------------ | -----------------------------------|-----------------------------------------|
| `DJANGO_SETTINGS_MODULE` | Django settings                    |Giữ nguyên                               |
| `GEMINI_API_KEY`         | API key dùng cho Google Gemini     |https://aistudio.google.com/api-keys     |
| `IMGBB_API_KEY`          | API upload ảnh                     |https://api.imgbb.com/                   |
| `EMAIL_USER`             | Gmail dùng để gửi mail             |https://myaccount.google.com/            |
| `EMAIL_PASS`             | Mật khẩu ứng dụng của 'EMAIL_USER  |https://myaccount.google.com/apppasswords|


👉 Thay:

```
YOUR_GEMINI_API: API KEY của GEMINI 2.5 FLASH (đề cử) 
YOUR_IMGBB_API: API từ trang web cho phép upload ảnh miễn phí
EMAIL_USER: gmail dùng để gửi gmail cho đăng nhập/đăng ký/ quên mật khẩu
EMAIL_PASS: mật khẩu ứng dụng cho phép bên thứ 3 truy cập và gửi gmail với người gửi là EMAIL_USER
```

bằng key thật của bạn.

---

## ▶️ Chạy project local

```bash
python manage.py migrate
python manage.py runserver
```

Truy cập:

```
http://127.0.0.1:8000/
```

---

## 🚀 Hướng dẫn chạy ứng dụng với Google App Engine (GAE)

Dự án này sử dụng môi trường Legacy (Python 2.7) và Google Cloud SDK. Để đảm bảo ứng dụng vận hành ổn định trên máy cục bộ, vui lòng tuân thủ các thông số cấu hình dưới đây.

### 1. Môi trường khuyến nghị (Prerequisites)

| Thành phần | Phiên bản yêu cầu |
| :--- | :--- |
| **Python** | 2.7.18 |
| **Django** | 1.11.29 |
| **Google Cloud SDK** | 357.0.0 |
| **app-engine-python** | 1.9.93 |
| **app-engine-python-extras** | 1.9.93 |
| **cloud-datastore-emulator** | 2.1.0 |
| **PyCharm IDE** | 2023.3.7 (Hoặc các bản cùng thời kỳ) |

---

### 2. Cấu hình chạy trên PyCharm

Sau khi cài đặt môi trường, thực hiện các bước sau để thiết lập trình chạy (Run Configuration):

1. Truy cập: **Edit Configurations** -> **Add New Configuration (+)** -> **App Engine Server**.
2. Thiết lập các thông số quan trọng trong bảng:
   * **Host:** `127.0.0.1`
   * **Port:** `8080`
   * **Working directory:** `'PATH-TO-REPO'` (Đường dẫn tới thư mục bạn đã clone project từ GitHub).

3. Tại mục **Additional options**, copy và dán đoạn mã sau (vui lòng thay đổi đường dẫn phù hợp):

```bash
--host=0.0.0.0 --enable_host_checking=false --storage_path='PATH-DATASTORE' --show_mail_body --log_level=warning --dev_appserver_log_level=debug 'PATH-TO-REPO'
```

Kiểm tra và tích chọn (Checkbox):

[x] Add content roots to PYTHONPATH

[x] Add source roots to PYTHONPATH

Nhấn Apply -> OK.

### 3. Giải thích các tham số cấu hình (Additional Options)

Hiểu rõ các tham số này sẽ giúp bạn kiểm soát môi trường phát triển hiệu quả hơn:

| Tham số | Ý nghĩa & Tác dụng |
| :--- | :--- |
| `--host=0.0.0.0` | Cho phép các thiết bị khác trong cùng mạng nội bộ (như điện thoại) truy cập vào app thông qua địa chỉ IP của máy bạn. |
| `--enable_host_checking=false` | Tắt kiểm tra bảo mật tên miền. Đây là tùy chọn bắt buộc phải đi kèm khi bạn sử dụng `--host=0.0.0.0`. |
| `--storage_path='PATH'` | Chỉ định đường dẫn lưu trữ dữ liệu Datastore. Nếu có tham số này, dữ liệu bạn đã tạo sẽ không bị mất khi tắt server. |
| `--show_mail_body` | Hiển thị nội dung email (ví dụ: mã OTP) trực tiếp tại cửa sổ Logs của PyCharm thay vì thực sự gửi email qua server SMTP. |
| `--log_level=warning` | Thiết lập mức độ ghi log của ứng dụng. Chỉ hiển thị các cảnh báo và lỗi để giữ cửa sổ console gọn gàng hơn. |
| `--dev_appserver_log_level=debug` | Thiết lập mức độ log của hệ thống server GAE. Hiển thị chi tiết cách server xử lý request hoặc các lỗi hệ thống sâu bên dưới. |

---

### 4. Các lựa chọn chạy ứng dụng (Run Options)

Tùy vào mục đích sử dụng, bạn có thể thay đổi dòng lệnh trong phần **Additional options** của PyCharm theo các gợi ý sau:

| Lựa chọn | Tên chế độ | Mô tả & Mục đích | Dòng lệnh (Additional Options) |
| :--- | :--- | :--- | :--- |
| **A** | **Tiêu chuẩn (Khuyên dùng)** | Phát triển tính năng bình thường, lưu dữ liệu, log hiển thị vừa đủ để theo dõi. | `--host=127.0.0.1 --storage_path='PATH-DATASTORE' --show_mail_body --log_level=info 'PATH-TO-REPO'` |
| **B** | **Dữ liệu sạch (Clean)** | Chạy ứng dụng như một người dùng mới hoàn toàn. Dữ liệu sẽ mất sạch sau khi bạn tắt server. | `--host=127.0.0.1 --show_mail_body --log_level=warning 'PATH-TO-REPO'` |
| **C** | **Debug sâu** | Sử dụng khi gặp lỗi khó hoặc cần soi chi tiết từng truy vấn vào Datastore. | `--host=127.0.0.1 --storage_path='PATH-DATASTORE' --show_mail_body --log_level=debug --dev_appserver_log_level=debug 'PATH-TO-REPO'` |
| **D** | **Kiểm tra di động** | Dùng khi muốn dùng điện thoại/máy tính bảng truy cập thử giao diện (Yêu cầu chung Wi-Fi). | `--host=0.0.0.0 --enable_host_checking=false --storage_path='PATH-DATASTORE' 'PATH-TO-REPO'` |

**Lưu ý quan trọng:** 
* Thay thế `'PATH-DATASTORE'` bằng đường dẫn thư mục chứa dữ liệu của bạn.
* Thay thế `'PATH-TO-REPO'` bằng đường dẫn tuyệt đối đến thư mục chứa file `app.yaml` của dự án.

---

## 📁 Cấu trúc project

```
D:\IMG2XLS\VN-KIET-DJANGO-TRAINING\IMG2XL_APP
│   admin.py
│   apps.py
│   urls.py
│   __init__.py
│
├───forms
│       register_form.py
│       upload_file_form.py
│       __init__.py
│
├───migrations
│       0001_initial.py
│       __init__.py
│
├───models
│       extracted_result.py
│       notification.py
│       uploaded_file.py
│       usage_log.py
│       user_profile.py
│       __init__.py
│
├───services
│       ai_extraction_images.py
│       ai_extraction_text.py
│       context_processors.py
│       sheets_export.py
│       table_handler.py
│       upload_image.py
│       __init__.py
│
├───static
│   └───img2xl_app
│       ├───css
│       │   │   bootstrap.css
│       │   │   documents.css
│       │   │   export_ui.css
│       │   │   footer.css
│       │   │   header.css
│       │   │   home.css
│       │   │   image_editor.css
│       │   │   result_detail.css
│       │   │   settings.css
│       │   │   trash_bin.css
│       │   │
│       │   ├───registration
│       │   │       login.css
│       │   │       register.css
│       │   │
│       │   └───settings
│       │           account.css
│       │           linkedAccount.css
│       │           password.css
│       │           profile.css
│       │
│       ├───js
│       │   ├───common
│       │   │       utils.js
│       │   │
│       │   ├───components
│       │   │   │   bootstrap.bundle.js
│       │   │   │   documents.js
│       │   │   │   export_ui.js
│       │   │   │   footer.js
│       │   │   │   header.js
│       │   │   │   image_handler.js
│       │   │   │   settings.js
│       │   │   │   trash_bin.js
│       │   │   │
│       │   │   ├───home
│       │   │   │       extractionHandler.js
│       │   │   │       filePreviewManager.js
│       │   │   │       historyManager.js
│       │   │   │       home.js
│       │   │   │
│       │   │   ├───registration
│       │   │   │       forgot_password.js
│       │   │   │       forgot_password_manager.js
│       │   │   │       login.js
│       │   │   │       register.js
│       │   │   │       register_manager.js
│       │   │   │
│       │   │   ├───result_detail
│       │   │   │       result_detail.js
│       │   │   │       spreadsheet_manager.js
│       │   │   │       table_actions.js
│       │   │   │
│       │   │   └───settings
│       │   │           account.js
│       │   │           linkedAccount.js
│       │   │           password.js
│       │   │           profile.js
│       │   │
│       │   └───services
│       │       │   document_service.js
│       │       │   home_service.js
│       │       │   notification_service.js
│       │       │   table_service.js
│       │       │   trash_bin_service.js
│       │       │
│       │       └───registration
│       │               auth_service.js
│       │
│       └───scss
│           │   documents.scss
│           │   export_ui.scss
│           │   footer.scss
│           │   header.scss
│           │   home.scss
│           │   image_editor.scss
│           │   result_detail.scss
│           │   settings.scss
│           │   trash_bin.scss
│           │
│           ├───registration
│           │       login.scss
│           │       register.scss
│           │
│           └───settings
│                   account.scss
│                   linkedAccount.scss
│                   password.scss
│                   profile.scss
│
├───templates
│   └───img2xl_app
│       │   base.html
│       │   documents.html
│       │   export_ui.html
│       │   home.html
│       │   result_detail.html
│       │   settings.html
│       │   trash_bin.html
│       │
│       ├───includes
│       │       export_ui.html
│       │       footer.html
│       │       header.html
│       │       image_editor.html
│       │       noti_list_items.html
│       │       table_tools.html
│       │
│       ├───registration
│       │       forgot_password.html
│       │       login.html
│       │       register.html
│       │
│       └───settings
│               account.html
│               linkedAccount.html
│               password.html
│               profile.html
│
├───tests
│       __init__.py
│
└───views
        auth.py
        auto_cleanup.py
        documents.py
        generate_images.py
        home.py
        notifications.py
        result_detail_table_exports.py
        result_detail_views.py
        settings.py
        trash_bin.py
        __init__.py

```

---

## ⚠️ Lưu ý

* Python 2.7 đã deprecated → chỉ dùng cho môi trường cũ
* Không commit `app.yaml` nếu chứa API key

---

## 👨‍💻 Đóng góp

Pull request luôn được chào đón 🚀


