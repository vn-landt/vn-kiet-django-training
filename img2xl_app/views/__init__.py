from home import home, delete_result

from result_detail_views import result_detail, update_table_data, generate_ai_content, generate_ai_images
from result_detail_table_exports import export, export_to_sheets

from trash_bin import trash_bin_view, restore_item_api
from notificaions import mark_as_read, delete_notification, mark_all_read, delete_all_notifications, toggle_read
from documents import documents_view, update_title_api, delete_result_api, delete_image_api, bulk_delete_images_api, update_image_info, bulk_update_time, create_spreadsheet_blank
from settings import settings_view, update_account_settings, update_profile_settings, change_password

from auto_cleanup import auto_cleanup_task
from auth import register, check_email_exists, send_otp, verify_otp_ajax, forgot_password_view, reset_password_final

## Words White because not used no problems
