# Generated by Django 4.1.2 on 2023-04-23 05:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0015_rename_image_productimage'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='image',
        ),
    ]
