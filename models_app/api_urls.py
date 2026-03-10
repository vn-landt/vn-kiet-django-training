from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from .views import AIModelViewSet

router = DefaultRouter()
router.register(r'aimodels', AIModelViewSet, basename='aimodel')

urlpatterns = [
    url('api/', include(router.urls)),
]