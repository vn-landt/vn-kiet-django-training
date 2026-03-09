from django.urls import path
from .views import (
    AIModelListView, AIModelDetailView, AIModelCreateView, AIModelUpdateView, AIModelDeleteView,
    home  # Giữ home FBV nếu muốn
)

app_name = 'models_app'

urlpatterns = [
    path('', home, name='home'),  # Giữ root là home (FBV)
    path('models/', AIModelListView.as_view(), name='aimodel_list'),
    path('models/<int:pk>/', AIModelDetailView.as_view(), name='aimodel_detail'),
    path('upload/', AIModelCreateView.as_view(), name='aimodel_create'),
    path('models/<int:pk>/update/', AIModelUpdateView.as_view(), name='aimodel_update'),
    path('models/<int:pk>/delete/', AIModelDeleteView.as_view(), name='aimodel_delete'),
]