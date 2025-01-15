from datetime import date, timedelta
from django.core.management.base import BaseCommand
from home.models import EMI, Expense, Category

class Command(BaseCommand):
    help = 'Processes EMI deductions and schedules next payments'

    def handle(self, *args, **kwargs):
        today = date.today()
        emis = EMI.objects.filter(next_payment_date__lte=today, status='Active')

        for emi in emis:
            # Create an expense for the EMI payment
            category, _ = Category.objects.get_or_create(
                user=emi.user,
                name="EMI Payments",
                category_type=Category.EXPENSE
            )

            Expense.objects.create(
                user=emi.user,
                amount=emi.amount,
                date=today,
                description=f"EMI Payment: {emi.description}",
                category=category
            )

            if emi.frequency == 'Custom Dates':
                custom_dates = emi.custom_payment_dates or []
                try:
                    next_date = next(d for d in custom_dates if d > today)
                    emi.next_payment_date = next_date
                except StopIteration:
                    emi.status = 'Completed'
                    emi.save()
                    self.stdout.write(f"EMI {emi.description} for user {emi.user.email} has been completed.")
                    continue

            elif emi.frequency == 'Custom Frequency':
                next_payment_date = emi.next_payment_date + timedelta(days=emi.custom_frequency_days or 0)
                if next_payment_date > emi.end_date:
                    emi.status = 'Completed'
                    emi.save()
                    self.stdout.write(f"EMI {emi.description} for user {emi.user.email} has been completed.")
                    continue
                else:
                    emi.next_payment_date = next_payment_date

            else:
                next_payment_date = {
                    'Daily': emi.next_payment_date + timedelta(days=1),
                    'Weekly': emi.next_payment_date + timedelta(days=7),
                    'Monthly': emi.next_payment_date + timedelta(days=30),
                }.get(emi.frequency, emi.next_payment_date + timedelta(days=30))

                if next_payment_date > emi.end_date:
                    emi.status = 'Completed'
                    emi.save()
                    self.stdout.write(f"EMI {emi.description} for user {emi.user.email} has been completed.")
                    continue
                else:
                    emi.next_payment_date = next_payment_date

            emi.save()

        self.stdout.write("EMI processing complete.")

