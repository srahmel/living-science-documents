from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'action', 'target_model', 'target_id', 'actor')
    list_filter = ('action', 'target_model')
    search_fields = ('action', 'target_model', 'target_id', 'actor__username')
    readonly_fields = ('created_at',)

# Register your models here.
