# Generated by Django 3.2.3 on 2024-05-21 18:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_remove_follow_created'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Follow',
        ),
    ]
