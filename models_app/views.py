from django.shortcuts import render, get_object_or_404, redirect
from .models import AIModel
from .forms import AIModelForm

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

def aimodel_create(request):
    if request.method == 'POST':
        form = AIModelForm(request.POST, request.FILES)  # request.FILES cho file upload
        if form.is_valid():
            form.save()
            return redirect('models_app:aimodel_list')  # Redirect sau khi save thành công
    else:
        form = AIModelForm()

    return render(request, 'models_app/aimodel_form.html', {
        'form': form,
        'title': 'Upload Model AI Mới',
    })