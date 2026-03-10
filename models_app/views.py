from __future__ import unicode_literals

import json
import urllib2  # Python 2 use urllib2 instead urllib.request

from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.template.context_processors import request
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin

try:
    from django.urls import reverse_lazy
except ImportError:
    from django.core.urlresolvers import reverse_lazy

from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)

from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

# Import from project
from .models import AIModel
from .forms import AIModelForm, RegisterForm
from .serializers import AIModelSerializer, PredictInputSerializer

# 1. ListView
class AIModelListView(ListView):
    model = AIModel
    template_name = 'models_app/aimodel_list.html'
    context_object_name = 'aimodels'
    ordering = ['-created_at']

# 2. DetailView
class AIModelDetailView(DetailView):
    model = AIModel
    template_name = 'models_app/aimodel_detail.html'
    context_object_name = 'aimodel'

# 3. CreateView
class AIModelCreateView(LoginRequiredMixin, CreateView):
    login_url = '/login/'
    model = AIModel
    form_class = AIModelForm
    template_name = 'models_app/aimodel_form.html'
    success_url = reverse_lazy('models_app:aimodel_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Upload New Model AI'
        return context


# 4. UpdateView
class AIModelUpdateView(UpdateView):
    model = AIModel
    form_class = AIModelForm
    template_name = 'models_app/aimodel_form.html'
    success_url = reverse_lazy('models_app:aimodel_list')

    def get_context_data(self, **kwargs):
        context = super(AIModelUpdateView, self).get_context_data(**kwargs)
        context['title'] = u'Settings: {0}'.format(self.object.name)
        return context

# 5. DeleteView
class AIModelDeleteView(DeleteView):
    model = AIModel
    template_name = 'models_app/aimodel_confirm_delete.html'  # Template
    success_url = reverse_lazy('models_app:aimodel_list')

    def get_context_data(self, **kwargs):
        context = super(AIModelDeleteView, self).get_context_data(**kwargs)
        context['title'] = u'Confirm Delete: {self.object.name}'
        return context

def home(request):
    return render(request, 'models_app/home.html', {'title': 'Welcome to AI Model Hub'})

# Login (generic)
class CustomLoginView(LoginView):
    template_name = 'models_app/login.html'
    redirect_authenticated_user = True

# Logout (generic)
def custom_logout(request):
    logout(request)
    return redirect('models_app:home')

# Register (CreateView)
class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'models_app/register.html'
    success_url = reverse_lazy('models_app:login')

class AIModelViewSet(viewsets.ModelViewSet):
    """
    API endpoint cho AIModel: list, create, retrieve, update, delete.
    """
    queryset = AIModel.objects.all().order_by('-created_at')
    serializer_class = AIModelSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        aimodel = self.get_object()
        if aimodel.model_file:
            return Response({'file_url': aimodel.model_file.url})
        return Response({'error': 'No file available'}, status=404)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def predict(self, request, pk=None):
        aimodel = self.get_object()

        if aimodel.model_type != 'gemini_ocr':
            return self.old_predict_logic(request, aimodel)

        # Gemini OCR/Table Extraction
        if 'image' not in request.FILES:
            return Response({"error": "Request Input 1 Image"}, status=400)

        image_file = request.FILES['image']
        image_content = image_file.read()
        base64_image = base64.b64encode(image_content)

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=" + settings.GEMINI_API_KEY

        prompt = """
        Extract the entire data table from this image as a JSON array of objects.
        Each object is a row, with the key being the column header.
        If no table is available, return the full text.
        """

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {
                        "mime_type": image_file.content_type or "image/jpeg",
                        "data": base64_image
                    }}
                ]
            }]
        }

        try:
            req = urllib2.Request(url, json.dumps(payload), {'Content-Type': 'application/json'})
            response = urllib2.urlopen(req)
            data = json.load(response)
            gemini_response = data['candidates'][0]['content']['parts'][0]['text']

            try:
                extracted_data = json.loads(gemini_response)
            except:
                extracted_data = {"text": gemini_response}

            from StringIO import StringIO
            import csv

            output = StringIO()
            writer = csv.writer(output)
            if isinstance(extracted_data, list):
                if extracted_data:
                    headers = extracted_data[0].keys()
                    writer.writerow(headers)
                    for row in extracted_data:
                        writer.writerow([row.get(h, '') for h in headers])
            else:
                writer.writerow(["Extracted Text"])
                writer.writerow([extracted_data.get('text', '')])

            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="extracted_data.csv"'
            return response

        except Exception as e:
            return Response({"error": str(e)}, status=500)