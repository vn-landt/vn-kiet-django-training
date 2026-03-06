from django.urls import path
from .views import aimodel_list, aimodel_detail

urlpatterns = [
    path('', aimodel_list, name='aimodel_list'),          # / → list
    path('<int:pk>/', aimodel_detail, name='aimodel_detail'),  # /1/, /2/,...
]