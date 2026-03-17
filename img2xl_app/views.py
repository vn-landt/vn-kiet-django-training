# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponse
from django.shortcuts import render

def home(request):
    return HttpResponse("""
        <h1>✅ Ngày 2 đã hoàn thành thành công!</h1>
        <p>Models đã được tạo và migrate OK.</p>
        <p>App img2xl_app đang chạy trên local.</p>
        <hr>
        <p><strong>Tiếp theo:</strong> Ngày 3 (Gemini REST API)</p>
    """)