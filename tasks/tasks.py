from cProfile import run
from configparser import SectionProxy
import datetime
import email
import time

from django.contrib.auth.models import User
from django.core.mail import send_mail
from tasks.models import Report, Task
from datetime import timedelta

from celery.decorators import periodic_task

from task_manager.celery import app


@periodic_task(run_every=timedelta(seconds=10))
def send_mail_reminder():
    now_time = datetime.datetime.now().time()
    now_date = datetime.date.today()
    # fetching reports for sent reports yesterday at the given time
    reports = Report.objects.filter(
        report_time__lte=now_time, report_date__lte=now_date - timedelta(days=1)
    )
    for report in reports:
        send_mail(report)


def send_mail(report):
    report_user = User.objects.filter(user=report.user)[0]
    pending_qs = Task.objects.filter(user=report_user, completed=False, deleted=False)
    email_context = f"You have {pending_qs.count()} Pending tasks"
    try:
        send_mail(
            "Pendning Task from Task Manager",
            email_context,
            "wolverine@wolverine.com",
            [report_user.email],
        )
        report.report_date = datetime.date.today()
        report.save()
    except:
        pass
