# Generated by Django 5.1.3 on 2024-11-30 14:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0005_emi_custom_frequency_days_alter_emi_frequency'),
    ]

    operations = [
        migrations.AddField(
            model_name='emi',
            name='status',
            field=models.CharField(choices=[('Active', 'Active'), ('Completed', 'Completed')], default='Active', max_length=10),
        ),
    ]
