from django.conf import settings
from django.db import models


class Evaluation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)
    expected_emission = models.FloatField()
    total_emission = models.FloatField()
    scope1_emission = models.FloatField(default=0)
    scope2_emission = models.FloatField(default=0)
    scope3_emission = models.FloatField(default=0)
    rows = models.JSONField(default=list)
    validation_issues = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
