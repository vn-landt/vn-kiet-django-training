from django.db import models


# FileField cho phép upload file model (sau này .pkl cho scikit-learn, .h5 cho Keras,...). upload_to='ai_models/' lưu vào folder media/ai_models/.
class AIModel(models.Model):
    name = models.CharField(max_length=200)  # Tên model, ví dụ: "Sentiment Analysis v1"
    description = models.TextField(blank=True)  # Mô tả chi tiết, cách dùng
    model_file = models.FileField(upload_to='ai_models/')  # File upload (sẽ config media sau)
    created_at = models.DateTimeField(auto_now_add=True)  # Tự động ngày tạo
    updated_at = models.DateTimeField(auto_now=True)     # Tự động update khi sửa

    def __str__(self):
        return self.name  # Hiển thị tên model đẹp trong admin/list

    class Meta:
        ordering = ['-created_at']  # Sắp xếp mới nhất trước