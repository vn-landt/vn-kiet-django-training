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

## 🧪 Tạo môi trường ảo

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

## 📚 Cài đặt thư viện

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
#application: ai-app-489908
#version: 1

runtime: python27
api_version: 1
threadsafe: yes

handlers:
- url: /static
  static_dir: static
- url: /media
  static_dir: media
- url: /.*
  script: main.application

libraries:
- name: django
  version: "1.11"
- name: PIL
  version: "1.1.7"
- name: ssl
  version: latest

env_variables:
  DJANGO_SETTINGS_MODULE: "img2xl_project.settings"
  GEMINI_API_KEY: "YOUR_GEMINI_API"
  IMGBB_API_KEY: "YOUR_IMGBB_API"

skip_files:
- ^(.*/)?#.*#$
- ^(.*/)?.*~$
- ^(.*/)?.*\.py[co]$
- ^(.*/)?.*/RCS/.*$
- ^(.*/)?\..*$
- ^\.idea/.*$
```

---

### 🔑 Giải thích biến môi trường

| Biến                     | Mô tả                          |
| ------------------------ | ------------------------------ |
| `GEMINI_API_KEY`         | API key dùng cho Google Gemini |
| `IMGBB_API_KEY`          | API upload ảnh                 |
| `DJANGO_SETTINGS_MODULE` | Django settings                |

👉 Thay:

```
YOUR_GEMINI_API
YOUR_IMGBB_API
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

## ☁️ Deploy (tuỳ chọn)

```bash
gcloud app deploy
```

---

## 📁 Cấu trúc project

```
vn-kiet-django-training/
│
├── img2xl_project/
├── static/
├── media/
├── requirements.txt
├── app.yaml.example
├── app.yaml
└── manage.py
```

---

## ⚠️ Lưu ý

* Python 2.7 đã deprecated → chỉ dùng cho môi trường cũ
* Không commit `app.yaml` nếu chứa API key

---

## 👨‍💻 Đóng góp

Pull request luôn được chào đón 🚀
