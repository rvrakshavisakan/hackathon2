from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='Evaluation', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('filename', models.CharField(max_length=255)), ('expected_emission', models.FloatField()), ('total_emission', models.FloatField()), ('scope1_emission', models.FloatField(default=0)), ('scope2_emission', models.FloatField(default=0)), ('scope3_emission', models.FloatField(default=0)), ('rows', models.JSONField(default=list)), ('validation_issues', models.JSONField(default=list)), ('created_at', models.DateTimeField(auto_now_add=True)), ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL))], options={'ordering': ['-created_at']})]
