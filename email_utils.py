import os
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta, date
import models

SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD')
MANAGER_EMAIL = os.environ.get('MANAGER_EMAIL')

def send_email(to_email, subject, body):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print('Email credentials not configured; skipping send.')
        return False

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print('Failed to send email:', e)
        return False


def send_shift_reminders_job():
    # Find shifts for tomorrow and email assigned volunteers
    conn = models.get_db()
    c = conn.cursor()
    tomorrow = date.today() + timedelta(days=1)
    c.execute("SELECT id, date, start_time, end_time, description FROM shifts WHERE date = ?", (tomorrow.isoformat(),))
    shifts = c.fetchall()

    for s in shifts:
        shift_id = s['id']
        c.execute("SELECT v.name, v.email FROM assignments a JOIN volunteers v ON a.volunteer_id = v.id WHERE a.shift_id = ?", (shift_id,))
        volunteers = c.fetchall()
        for v in volunteers:
            subject = f"Reminder: Upcoming shift on {s['date']}"
            body = f"Hi {v['name']},\n\nThis is a reminder for your recycling shift on {s['date']} from {s['start_time']} to {s['end_time']}.\n\nThanks for volunteering!"
            send_email(v['email'], subject, body)

    # Optionally notify manager with summary
    if MANAGER_EMAIL:
        c.execute("SELECT COUNT(*) as cnt FROM assignments WHERE shift_id IN (SELECT id FROM shifts WHERE date = ?)", (tomorrow.isoformat(),))
        cnt = c.fetchone()['cnt']
        send_email(MANAGER_EMAIL, f"Shifts for {tomorrow.isoformat()}", f"Total assignments tomorrow: {cnt}")

    conn.close()
