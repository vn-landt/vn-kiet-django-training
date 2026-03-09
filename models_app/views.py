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
from .serializers import AIModelSerializer


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