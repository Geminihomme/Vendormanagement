"""
BACKGROUND SCHEDULER (The "Alarm Clock")
==========================================
This file sets up an automated job that runs every day to check
for expiring contracts and send notification emails.

WHAT IS A BACKGROUND JOB?
===========================
Normally, our backend only does things when a user clicks something
(like "Add Vendor"). But some tasks need to happen AUTOMATICALLY,
even when nobody is using the app. That's a background job.

REAL-WORLD ANALOGY - The Night Security Guard:
Your office building has a security guard who makes rounds every night.
They check all the doors, write a report, and flag anything unusual.
They do this whether or not anyone is in the building.

Our background job is like that guard:
- It "wakes up" at 8:00 AM every day
- It checks all contracts for upcoming expirations
- It creates notifications and sends emails
- It does this automatically, forever

HOW DOES THE COMPUTER "KNOW" TO CHECK EVERY DAY?
===================================================
We use a library called APScheduler (Advanced Python Scheduler).
Think of it as setting an alarm clock inside your app:

  "Hey APScheduler, run this function every day at 8 AM."

Under the hood, APScheduler keeps track of time and triggers
the function when the clock hits the scheduled time. It's like
a cron job (a Linux scheduling tool) but built into Python.

CRON JOBS - A BRIEF HISTORY:
"cron" is a Unix/Linux tool from 1975 that runs commands on a schedule.
The name comes from "chronos" (Greek for time). System admins use cron
to automate backups, cleanup, and reports. APScheduler gives us the
same power inside our Python app.

WHAT HAPPENS IF THE SERVER RESTARTS?
When the server starts up, the scheduler starts too. It doesn't
"remember" that it missed yesterday's check while the server was off.
For our use case, that's fine — the next day's check will catch
everything because we look at date ranges (30/60/90 days), not
specific dates.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import SessionLocal
from app.services import notification_service, email_service

logger = logging.getLogger(__name__)

# Create the scheduler instance.
# BackgroundScheduler runs in a separate thread so it doesn't block
# the web server from handling normal requests.
scheduler = BackgroundScheduler()


def run_expiry_check():
    """
    The function that runs every day. This is the "security guard's patrol."

    Steps:
    1. Open a database connection
    2. Check all contracts for upcoming expirations
    3. Send emails for any new notifications
    4. Close the database connection
    5. Log what happened (for debugging)

    WHY do we open/close the database connection here?
    Background jobs don't go through the normal web request pipeline
    (which handles DB connections automatically via get_db()).
    So we have to manage the connection ourselves.
    It's like the security guard bringing their own flashlight
    instead of using the office lights.
    """
    logger.info("Starting daily contract expiration check...")

    # Open a database session
    db = SessionLocal()
    try:
        # Step 1: Find expiring contracts and create notifications
        new_notifications = notification_service.check_expiring_contracts(db)

        if new_notifications:
            logger.info(
                f"Found {len(new_notifications)} new expiring contract alerts"
            )

            # Step 2: Send emails for each new notification
            email_results = email_service.send_batch_notifications(
                new_notifications
            )
            logger.info(
                f"Email results: {email_results['sent']} sent, "
                f"{email_results['failed']} failed, "
                f"{email_results['skipped']} skipped (no recipient)"
            )

            # Step 3: Mark notifications as email_sent in database
            for notif_data in new_notifications:
                # Find the notification we just created and mark email_sent
                from app.models.notification import Notification
                notif = db.query(Notification).filter(
                    Notification.contract_id == notif_data["contract_id"],
                    Notification.notification_type == notif_data["type"],
                ).order_by(Notification.created_at.desc()).first()

                if notif and notif_data.get("recipient_email"):
                    notif.email_sent = True

            db.commit()
        else:
            logger.info("No new contract expiration alerts today.")

    except Exception as e:
        logger.error(f"Error during expiration check: {e}")
        db.rollback()
    finally:
        db.close()

    logger.info("Daily contract expiration check complete.")


def start_scheduler():
    """
    Start the background scheduler when the app boots up.

    The CronTrigger(hour=8, minute=0) means:
    "Run at 8:00 AM every day"

    This is like setting an alarm clock:
    - hour=8: The hour (8 AM)
    - minute=0: The minute (on the dot)
    - No day/month specified = every day

    You could also schedule it differently:
    - CronTrigger(hour=8, day_of_week='mon-fri') = weekdays only
    - CronTrigger(hour='*/6') = every 6 hours
    - CronTrigger(hour=8, day=1) = 1st of every month
    """
    scheduler.add_job(
        run_expiry_check,
        trigger=CronTrigger(hour=8, minute=0),
        id="daily_expiry_check",
        name="Check for expiring contracts",
        replace_existing=True,  # If the job already exists, replace it
    )

    scheduler.start()
    logger.info("Background scheduler started. Daily check scheduled for 8:00 AM.")


def stop_scheduler():
    """Gracefully shut down the scheduler when the app stops."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler stopped.")
