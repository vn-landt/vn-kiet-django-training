from rest_framework import serializers
from .models import AIModel

class AIModelSerializer(serializers.ModelSerializer):
    model_file_url = serializers.SerializerMethodField()  # Giữ nguyên

    def get_model_file_url(self, obj):
        if obj.model_file:
            return obj.model_file.url
        return None

    class Meta:
        model = AIModel
        fields = [
            'id',
            'name',
            'description',
            'model_file',
            'model_file_url',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']