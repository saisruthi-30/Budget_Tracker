# Generated by Django 5.1.3 on 2024-11-18 09:13

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='category_type',
            field=models.CharField(choices=[('Income', 'Income'), ('Expense', 'Expense')], default='Income', max_length=10),
        ),
        migrations.AlterUniqueTogether(
            name='category',
            unique_together={('user', 'name', 'category_type')},
        ),
    ]
