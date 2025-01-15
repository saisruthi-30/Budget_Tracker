from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.core.management import call_command


def start_scheduler():
    scheduler = BackgroundScheduler()

    # Process EMI logic 
    scheduler.add_job(
        lambda: call_command('process_emi'),  # Trigger your existing command
        trigger=IntervalTrigger(minutes=1),  # Runs every minute
        id='process_emi',
        replace_existing=True
    )

    # Send EMI notifications for upcoming payments
    scheduler.add_job(
        lambda: call_command('send_emi_notifications'),  # Trigger new notification command
        # trigger=IntervalTrigger(days=1),  # Runs daily
         trigger=IntervalTrigger(minutes=1),  # Runs Every Minute
        id='send_emi_notifications',
        replace_existing=True
    )

    # Start the scheduler
    scheduler.start()

