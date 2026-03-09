from django import forms
from .models import AIModel

class AIModelForm(forms.ModelForm):
    class Meta:
        model = AIModel
        fields = ['name', 'description', 'model_file']  # Các field cho phép upload

        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'model_file': forms.FileInput(),
        }

    def clean_model_file(self):
        file = self.cleaned_data.get('model_file')
        if file:
            # Optional: Validate extension (ví dụ chỉ cho .pkl, .h5, .joblib)
            allowed_extensions = ['.pkl', '.h5', '.joblib', '.pt']
            ext = file.name.lower()[-5:] if len(file.name) > 5 else file.name.lower()
            if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
                raise forms.ValidationError("Chỉ chấp nhận file .pkl, .h5, .joblib, .pt")
        return file