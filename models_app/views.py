from django.template.context_processors import request
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import AIModel
from .forms import AIModelForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView
from .forms import RegisterForm
from django.contrib.auth import logout
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .serializers import AIModelSerializer, PredictInputSerializer
from rest_framework import status
import joblib
import os
from django.conf import settings


# 1. ListView cho danh sách AIModel
class AIModelListView(ListView):
    model = AIModel
    template_name = 'models_app/aimodel_list.html'
    context_object_name = 'aimodels'  # Tên biến trong template (thay vì object_list)
    ordering = ['-created_at']  # Sắp xếp mới nhất trước

# 2. DetailView cho chi tiết
class AIModelDetailView(DetailView):
    model = AIModel
    template_name = 'models_app/aimodel_detail.html'
    context_object_name = 'aimodel'

# 3. CreateView cho upload mới
class AIModelCreateView(LoginRequiredMixin, CreateView):
    login_url = '/login/'
    model = AIModel
    form_class = AIModelForm  # Dùng form đã tạo ở phần 7
    template_name = 'models_app/aimodel_form.html'
    success_url = reverse_lazy('models_app:aimodel_list')  # Redirect sau save

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Upload Model AI Mới'
        return context

# 4. UpdateView: Chỉnh sửa AIModel
class AIModelUpdateView(UpdateView):
    model = AIModel
    form_class = AIModelForm
    template_name = 'models_app/aimodel_form.html'  # Dùng chung template với create
    success_url = reverse_lazy('models_app:aimodel_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Chỉnh sửa: {self.object.name}'
        return context

# 5. DeleteView: Xóa AIModel
class AIModelDeleteView(DeleteView):
    model = AIModel
    template_name = 'models_app/aimodel_confirm_delete.html'  # Template confirm riêng
    success_url = reverse_lazy('models_app:aimodel_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Xác nhận xóa: {self.object.name}'
        return context

def home(request):
    return render(request, 'models_app/home.html', {'title': 'Chào mừng đến AI Model Hub'})

# Login (generic)
class CustomLoginView(LoginView):
    template_name = 'models_app/login.html'
    redirect_authenticated_user = True  # Nếu đã login thì redirect

# Logout (generic)
def custom_logout(request):
    logout(request)
    return redirect('models_app:home')  # hoặc redirect('/')

# Register (CreateView)
class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'models_app/register.html'
    success_url = reverse_lazy('models_app:login')

class AIModelViewSet(viewsets.ModelViewSet):
    """
    API endpoint cho AIModel: list, create, retrieve, update, delete.
    """
    queryset = AIModel.objects.all().order_by('-created_at')
    serializer_class = AIModelSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  # Read: ai cũng được, Write: phải login

    # Optional: Filter theo user nếu sau này add owner field
    # def get_queryset(self):
    #     if self.request.user.is_authenticated:
    #         return AIModel.objects.filter(owner=self.request.user)
    #     return AIModel.objects.none()  # Hoặc public

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        aimodel = self.get_object()
        if aimodel.model_file:
            return Response({'file_url': aimodel.model_file.url})
        return Response({'error': 'No file available'}, status=404)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def predict(self, request, pk=None):
        aimodel = self.get_object()

        file_path = aimodel.model_file.path
        if not os.path.exists(file_path):
            return Response({"error": "Model file not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            model = joblib.load(file_path)  # Load Iris model (scikit-learn)
        except Exception as e:
            return Response({"error": f"Load model failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Input cho Iris: 4 features số
        serializer = PredictInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Giả sử input là list 4 số (từ serializer)
        features = serializer.validated_data.get('features')  # Thêm field này ở serializer
        if not features or len(features) != 4:
            return Response({"error": "Input phải là mảng 4 số (sepal_length, sepal_width, petal_length, petal_width)"},
                            status=400)

        try:
            # Predict: input là [[...]] vì scikit-learn expect 2D array
            prediction = model.predict([features])[0]
            probability = model.predict_proba([features])[0] if hasattr(model, 'predict_proba') else None

            # Map class sang tên hoa (Iris chuẩn)
            iris_classes = ["setosa", "versicolor", "virginica"]
            result = {
                "predicted_class": iris_classes[prediction],
                "class_id": int(prediction),
                "probability": probability.tolist() if probability is not None else None,
                "input_features": features,
                "model_name": aimodel.name
            }
        except Exception as e:
            return Response({"error": f"Predict failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(result, status=status.HTTP_200_OK)