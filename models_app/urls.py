from django.urls import path
from .views import aimodel_list, aimodel_detail, home  # Đảm bảo import home

app_name = 'models_app'

urlpatterns = [
    path('', home, name='home'),  # Root '/' → home view
    path('home/', home, name='home_explicit'),  # Optional: Giữ /home/ nếu muốn
    path('models/', aimodel_list, name='aimodel_list'),  # Đổi prefix cho list/detail để tránh conflict
    path('models/<int:pk>/', aimodel_detail, name='aimodel_detail'),
]