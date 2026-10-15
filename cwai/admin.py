from django.contrib import admin
from .models import Evaluation

@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "filename", "total_emission", "created_at")
    list_filter = ("created_at",)
    search_fields = ("filename", "user__username")
