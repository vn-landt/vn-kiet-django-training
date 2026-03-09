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

class PredictInputSerializer(serializers.Serializer):
    features = serializers.ListField(
        child=serializers.FloatField(),
        min_length=4,
        max_length=4,
        required=True,
        help_text="Mảng 4 số: [sepal_length, sepal_width, petal_length, petal_width]"
    )