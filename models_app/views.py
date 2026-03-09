from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import AIModel
from .forms import AIModelForm
from django.shortcuts import render, get_object_or_404, redirect

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
class AIModelCreateView(CreateView):
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
