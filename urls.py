from django.conf.urls import url, include

urlpatterns = [
	url(r'^', include('ai_model_hub.urls')),
]
