# Generated by Django 4.1.2 on 2023-04-23 19:50

from django.db import migrations
import imagekit.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0020_brand_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='brand',
            name='image',
            field=imagekit.models.fields.ProcessedImageField(null=True, upload_to='brand'),
        ),
    ]
