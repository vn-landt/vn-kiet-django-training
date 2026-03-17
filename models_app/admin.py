from django.contrib import admin
from .models import AIModel

@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):

    list_display = ('name', 'created_at', 'updated_at')


    search_fields = ('name', 'description')


    list_filter = ('created_at',)


    ordering = ('-created_at',)
