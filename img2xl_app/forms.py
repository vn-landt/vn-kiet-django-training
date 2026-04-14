# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class UploadFileForm(forms.Form):
    file = forms.FileField(
        label='Select file',
        help_text='Supported formats: jpg, jpeg, png, pdf (max 10MB)'
    )

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email")