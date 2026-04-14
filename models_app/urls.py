from django.conf.urls import url
from .views import (
    AIModelListView, AIModelDetailView, AIModelCreateView, AIModelUpdateView, AIModelDeleteView,
    CustomLoginView, RegisterView,
    home, custom_logout
)
from django.urls import reverse_lazy
from django.contrib.auth.views import LogoutView

app_name = 'models_app'
APPEND_SLASH = False

urlpatterns = [
    url('login/', CustomLoginView.as_view(), name='login'),
    url('logout/', custom_logout, name='logout'),
    url('register/', RegisterView.as_view(), name='register'),
    url(r'^$', home, name='home'),
    url('models/', AIModelListView.as_view(), name='aimodel_list'),
    url('models/<int:pk>/', AIModelDetailView.as_view(), name='aimodel_detail'),
    url('upload/', AIModelCreateView.as_view(), name='aimodel_create'),
    url('models/<int:pk>/update/', AIModelUpdateView.as_view(), name='aimodel_update'),
    url('models/<int:pk>/delete/', AIModelDeleteView.as_view(), name='aimodel_delete'),
]