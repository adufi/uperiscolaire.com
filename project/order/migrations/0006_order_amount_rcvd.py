# Generated by Django 3.1.5 on 2021-02-10 15:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0005_order_amount_refunded'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='amount_rcvd',
            field=models.FloatField(default=0.0),
        ),
    ]