# Generated by Django 4.1.2 on 2023-05-02 14:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0025_brand_slug_category_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='instrumenttype',
            name='slug',
            field=models.SlugField(blank=True, null=True, unique=True),
        ),
    ]
