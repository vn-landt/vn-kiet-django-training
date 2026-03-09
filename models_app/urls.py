from django.urls import path
from .views import (
    AIModelListView, AIModelDetailView, AIModelCreateView, AIModelUpdateView, AIModelDeleteView,
    CustomLoginView, RegisterView,
    home, custom_logout  # Giữ home FBV nếu muốn
)
from django.urls import reverse_lazy
from django.contrib.auth.views import LogoutView

app_name = 'models_app'
APPEND_SLASH = False

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', custom_logout, name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('', home, name='home'),  # Giữ root là home (FBV)
    path('models/', AIModelListView.as_view(), name='aimodel_list'),
    path('models/<int:pk>/', AIModelDetailView.as_view(), name='aimodel_detail'),
    path('upload/', AIModelCreateView.as_view(), name='aimodel_create'),
    path('models/<int:pk>/update/', AIModelUpdateView.as_view(), name='aimodel_update'),
    path('models/<int:pk>/delete/', AIModelDeleteView.as_view(), name='aimodel_delete'),
]