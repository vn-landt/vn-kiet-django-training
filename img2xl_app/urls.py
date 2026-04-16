# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls import url
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    url(r'^register/$', views.register, name='register'),
    url(r'^check-email/$', views.check_email_exists, name='check_email_exists'),
    url(r'^send-otp/$', views.send_otp, name='send_otp'),
    url(r'^verify-otp-ajax/$', views.verify_otp_ajax, name='verify_otp_ajax'),
    url(r'^login/$', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    url(r'^logout/$', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    url(r'^forgot-password/$', views.forgot_password_view, name='forgot_password'),
    url(r'^reset-password-final/$', views.reset_password_final, name='reset_password_final'),
    url(r'^$', views.home, name='home'),
    url(r'^result/(?P<result_id>\d+)/$', views.result_detail, name='result_detail'),
    url(r'^home/delete/(?P<result_id>\d+)/$', views.delete_result, name='delete_result'),
    url(r'^export/(?P<result_id>\d+)/$', views.export, name='export'),
    url(r'^export_to_sheets/(?P<result_id>\d+)/$', views.export_to_sheets, name='export_to_sheets'),
    url(r'^result/(?P<result_id>\d+)/update/$', views.update_table_data, name='update_table_data'),
    
    # Trích xuất text với AI
    url(r'^api/generate-ai-content/$', views.generate_ai_content, name='generate_ai_content'),

    # Trích xuất ảnh với gemini
    url(r'^extract-only-api/$', views.generate_ai_images, name='extract_only_api'),
    url(r'^batch-extract-api/$', views.generate_ai_images, name='batch_extract_api'),

    url(r'^tasks/auto-cleanup/$', views.auto_cleanup_task, name='cleanup_old_data'),
    url(r'^documents/$', views.documents_view, name='documents'),
    url(r'^settings/$', views.settings_view, name='settings'),

    # documents and home
    url(r'^create-spreadsheet-blank/$', views.create_spreadsheet_blank, name='create_spreadsheet_blank'),

    # documents.html
    # 1. API cho Bảng tính từ documents.js (ExtractedResult)
    url(r'^documents/update-title/(?P<result_id>\d+)/$', views.update_title_api, name='update_title_api'),
    url(r'^documents/delete-result/(?P<result_id>\d+)/$', views.delete_result_api, name='delete_result_api'),
    # 2. API cho Hình ảnh từ documents.js (UploadedFile)
    url(r'^documents/delete-image/(?P<img_id>\d+)/$', views.delete_image_api, name='delete_image_api'),
    url(r'^documents/bulk-delete-images/$', views.bulk_delete_images_api, name='bulk_delete_images_api'),
    url(r'^documents/update-image-info/$', views.update_image_info, name='update_image_info'),
    url(r'^documents/bulk-update-time/$', views.bulk_update_time, name='bulk_update_time'),

    # settings
    url(r'^settings/update-account/$', views.update_account_settings, name='update_account_settings'),
    url(r'^settings/update-profile/$', views.update_profile_settings, name='update_profile_settings'),
    url(r'^settings/password/$', views.change_password, name='change_password'),

    # Notifications
    url(r'^notifications/mark-read/(?P<noti_id>\d+)/$', views.mark_as_read, name='mark_as_read'),
    url(r'^notifications/delete/(?P<noti_id>\d+)/$', views.delete_notification, name='delete_notification'),
    url(r'^notifications/mark-all-read/$', views.mark_all_read, name='mark_all_read'),
    url(r'^notifications/delete-all/$', views.delete_all_notifications, name='delete_all_notifications'),
    url(r'^notifications/toggle-read/(?P<noti_id>\d+)/$', views.toggle_read, name='toggle_read'),

    # Trash/Bin
    url(r'^trash-bin/$', views.trash_bin_view, name='trash_bin'),
    url(r'^trash-bin/api/restore/$', views.restore_item_api, name='restore_item_api'),
]