# Generated by Django 3.1.5 on 2021-02-10 14:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0004_remove_order_amount_refunded'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='amount_refunded',
            field=models.FloatField(blank=True, default=0.0),
        ),
    ]
