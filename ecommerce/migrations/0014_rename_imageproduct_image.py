# Generated by Django 4.1.2 on 2023-04-23 05:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0013_alter_imageproduct_product'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ImageProduct',
            new_name='Image',
        ),
    ]