# Generated by Django 5.1.3 on 2024-12-24 12:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0010_contactus_newslettersubscriber'),
    ]

    operations = [
        migrations.AddField(
            model_name='emi',
            name='notified',
            field=models.BooleanField(default=False),
        ),
    ]
