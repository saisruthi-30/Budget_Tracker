from django.core.management.base import BaseCommand
from datetime import date, timedelta
from home.models import EMI
from home.views import send_upcoming_emi_email

class Command(BaseCommand):
    help = "Send notifications for upcoming EMI payments."

    def handle(self, *args, **kwargs):
        today = date.today()
        upcoming_emis = EMI.objects.filter(
            next_payment_date__lte=today + timedelta(days=3),  # Notify 3 days before
            status='Active',
            notified=False  # Only send notifications for non-notified EMIs
        )

        for emi in upcoming_emis:
            if send_upcoming_emi_email(emi.user, emi):
                emi.notified = True  # Mark EMI as notified
                emi.save()

        self.stdout.write(self.style.SUCCESS(f"Processed {len(upcoming_emis)} EMIs"))
