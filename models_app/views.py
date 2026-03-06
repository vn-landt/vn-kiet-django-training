from django.shortcuts import render, get_object_or_404
from .models import AIModel

# Function-Based View: List tất cả AIModel
def aimodel_list(request):
    models = AIModel.objects.all().order_by('-created_at')  # Lấy tất cả, sắp xếp mới nhất trước
    context = {
        'aimodels': models,
        'title': 'AI Model Hub - Danh sách Model AI',
    }
    return render(request, 'models_app/aimodel_list.html', context)
    # render: Trả template + context data

# Function-Based View: Detail một AIModel (theo ID)
def aimodel_detail(request, pk):
    model_obj = get_object_or_404(AIModel, pk=pk)  # Lấy object hoặc 404 nếu không tồn tại
    context = {
        'aimodel': model_obj,
        'title': f'{model_obj.name} - Chi tiết',
    }
    return render(request, 'models_app/aimodel_detail.html', context)

def home(request):
    return render(request, 'models_app/home.html', {'title': 'Chào mừng đến AI Model Hub'})