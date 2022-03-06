# Generated by Django 4.0.1 on 2022-03-06 05:11

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('tasks', '0005_task_priority'),
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('report_time', models.TimeField(default=datetime.time(9, 0))),
                ('report_date', models.DateField(default=datetime.date.today, null=True)),
            ],
        ),
    ]
