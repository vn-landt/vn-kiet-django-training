from django.db import models


class AIModel(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    model_file = models.FileField(upload_to='ai_models/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']

    model_type = models.CharField(max_length=50, default='custom', choices=[
        ('custom', 'Custom Model (joblib/pkl)'),
        ('gemini_ocr', 'Gemini OCR/Table Extraction'),
    ])