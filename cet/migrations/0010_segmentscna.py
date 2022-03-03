# Generated by Django 3.2 on 2021-08-18 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cet', '0009_pdf_fast_v2'),
    ]

    operations = [
        migrations.CreateModel(
            name='segmentsCna',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.DecimalField(decimal_places=0, max_digits=10)),
                ('name', models.CharField(max_length=50)),
                ('is_total', models.CharField(max_length=1)),
            ],
        ),
    ]
