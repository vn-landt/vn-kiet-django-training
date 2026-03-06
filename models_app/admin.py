from django.contrib import admin
from .models import AIModel

@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    # Hiển thị các cột trong list view
    list_display = ('name', 'created_at', 'updated_at')  # Các field bạn muốn thấy ngay

    # Thêm search box (tìm theo name hoặc description)
    search_fields = ('name', 'description')

    # Thêm filter sidebar (lọc theo ngày tạo, ví dụ)
    list_filter = ('created_at',)

    # Sắp xếp mặc định: mới nhất trước
    ordering = ('-created_at',)

    # Nếu muốn hiển thị description ngắn (không full text)
    # list_display_links = ('name',)  # Click name để edit