# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^result/(?P<result_id>\d+)/$', views.result_detail, name='result_detail'),
    url(r'^download/(?P<result_id>\d+)/$', views.download_csv, name='download_csv'),
    url(r'^export/(?P<result_id>\d+)/$', views.export_to_sheets, name='export_to_sheets'),
]