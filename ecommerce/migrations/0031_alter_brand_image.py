# Generated by Django 4.1.2 on 2023-05-04 18:33

from django.db import migrations
import imagekit.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0030_alter_product_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='brand',
            name='image',
            field=imagekit.models.fields.ProcessedImageField(blank=True, null=True, upload_to='brand'),
        ),
    ]
