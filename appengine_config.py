# -*- coding: utf-8 -*-
import os

# "Đánh lừa" gspread bằng cách tạo biến APPDATA ảo
if 'APPDATA' not in os.environ:
    os.environ['APPDATA'] = os.path.expanduser("~")

# Giữ nguyên phần khai báo thư mục lib cũ của bạn
from google.appengine.ext import vendor
vendor.add(os.path.join(os.path.dirname(__file__), 'lib'))