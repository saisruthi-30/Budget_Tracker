# Generated by Django 5.1.3 on 2024-11-29 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_alter_category_category_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='emi',
            name='custom_payment_dates',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='emi',
            name='frequency',
            field=models.CharField(choices=[('Daily', 'Daily'), ('Weekly', 'Weekly'), ('Monthly', 'Monthly'), ('Custom', 'Custom')], max_length=20),
        ),
    ]
