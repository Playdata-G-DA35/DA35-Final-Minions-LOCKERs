# Generated by Django 4.2.15 on 2024-08-23 04:56

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("login", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="users",
            name="id",
        ),
        migrations.AddField(
            model_name="users",
            name="name",
            field=models.CharField(
                default="default_name", max_length=50, verbose_name="사용자이름"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="users",
            name="phone",
            field=models.CharField(
                blank=True,
                max_length=20,
                null=True,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        regex="^01([0|1|6|7|8|9]?)-?([0-9]{3,4})-?([0-9]{4})$"
                    )
                ],
            ),
        ),
    ]
