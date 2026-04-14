# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^result/(?P<result_id>\d+)/$', views.result_detail, name='result_detail'),
    url(r'^download/(?P<result_id>\d+)/$', views.download_csv, name='download_csv'),
    url(r'^export/(?P<result_id>\d+)/$', views.export_to_sheets, name='export_to_sheets'),
    url(r'^delete/(?P<result_id>\d+)/$', views.delete_result, name='delete_result'),
    url(r'^result/(?P<result_id>\d+)/save/$', views.update_table_data, name='update_table_data'),
    url(r'^api/generate-ai-content/$', views.ai_generate_view, name='ai_generate_content'),
]