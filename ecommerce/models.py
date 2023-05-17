from datetime import datetime
from django.db import models
from django.utils.text import slugify
from imagekit.models import ProcessedImageField
from django.utils.timezone import now
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser,Group, Permission

import os

# Create your models here.
class Customer(models.Model):
    name = models.CharField(max_length=30, null=False, blank=False)
    phone_number = models.CharField(max_length=11, unique=True, blank=False)
    email = models.EmailField(unique=True, blank=False)
    password = models.CharField(max_length=255, null=False, blank=False)
    shipping_address = models.CharField(max_length=255, null=True, blank=True)
    is_verify = models.BooleanField(default=False, null=True, blank=True)
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the customer_name field in associated PurchaseOrder models
        self.purchaseorder_set.update(customer_name=self.name)

class Brand(models.Model):
    name = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    image = ProcessedImageField(upload_to='static/images/brand',
                                format='JPEG',
                                options={'quality': 60},
                                null=True, blank = True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Brand, self).save(*args, **kwargs)
    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url
@receiver(pre_save, sender=Brand)
def delete_old_image(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_image = sender.objects.get(pk=instance.pk).image
        except sender.DoesNotExist:
            return
        new_image = instance.image
        if old_image and old_image != new_image:
            if os.path.isfile(old_image.path):
                os.remove(old_image.path)
@receiver(post_delete, sender=Brand)
def delete_image_file(sender, instance, **kwargs):
    image = instance.image
    if image and os.path.isfile(image.path):
        os.remove(image.path)

class InstrumentType(models.Model):
    name = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(InstrumentType, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(unique=True, null=True, blank=True)
    type = models.ForeignKey(InstrumentType, on_delete=models.SET_NULL, null=True, blank=True)
    display_home = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=11, decimal_places=2)
    description = models.TextField(null=True, blank=True)
    tech_param = models.TextField(null=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_feature = models.BooleanField(default=False)
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.importorderitem_set.update(product_name=self.name)
        super(Product, self).save(*args, **kwargs)
    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='static/images/product')

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url
@receiver(pre_save, sender=ProductImage)
def delete_old_image(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_image = sender.objects.get(pk=instance.pk).image
        except sender.DoesNotExist:
            return
        new_image = instance.image
        if old_image and old_image != new_image:
            if os.path.isfile(old_image.path):
                os.remove(old_image.path)
@receiver(post_delete, sender=ProductImage)
def delete_image_file(sender, instance, **kwargs):
    image = instance.image
    if image and os.path.isfile(image.path):
        os.remove(image.path)

class Supplier(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=11, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)

    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.importorder_set.update(supplier_name=self.name, supplier_phone=self.phone_number)


class ImportOrder(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    supplier_name = models.CharField(max_length=100, null=True)
    supplier_phone = models.CharField(max_length=11, null=True)

    def save(self, *args, **kwargs):
        if self.supplier:
            self.supplier_name = self.supplier.name
            self.supplier_phone = self.supplier.phone_number
        super(ImportOrder, self).save(*args, **kwargs)

    def __str__(self):
        return f"DN#{self.id}"


class ImportOrderItem(models.Model):
    import_order = models.ForeignKey(ImportOrder, null=True, on_delete=models.CASCADE,
                                     related_name='import_order_items')
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    quantity = models.PositiveIntegerField(null=False, blank=False)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product_name = models.CharField(max_length=100, null=True)

    def save(self, *args, **kwargs):
        if self.product:
            self.product_name = self.product.name
        super(ImportOrderItem, self).save(*args, **kwargs)

    def __str__(self):
        return self.product.name


class PurchaseOrder(models.Model):
    customer = models.ForeignKey(Customer, null=True, on_delete=models.SET_NULL)
    customer_name = models.CharField(max_length=30, null=True)
    receiver_name = models.CharField(max_length=30, null=True)
    customer_phone = models.CharField(max_length=11, null=True)
    receiver_phone = models.CharField(max_length=11, null=True)
    ordered_time = models.DateTimeField(auto_now_add=True)
    confirmed_time = models.DateTimeField(null=True, blank=True)
    shipped_time = models.DateTimeField(null=True, blank=True)
    shipping_address = models.TextField(null=True, blank = True)
    CHOICE_STATUS = (("PENDING", "Chờ xác nhận"),
                     ("DELIVERING", "Đang giao"),
                     ("DELIVERED", "Đã giao"),
                     ("CANCELED", "Đã hủy"))
    status = models.CharField(max_length=20, choices=CHOICE_STATUS)

    def save(self, *args, **kwargs):
        if self.customer:
            self.customer_name = self.customer.name
            self.customer_phone = self.customer.phone_number
        if self.pk:
            old_status = self.__class__.objects.get(pk=self.pk).status
            if old_status == 'PENDING':
                if self.status == 'DELIVERING':
                    self.confirmed_time = datetime.now()
                elif self.status != 'CANCELED':
                    self.status = old_status
            elif old_status == 'DELIVERING':
                if self.status == 'DELIVERED':
                    self.shipped_time = datetime.now()
                else:
                    self.status = old_status
            else:
                self.status = old_status
        super(PurchaseOrder, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.id}"


class PurchaseOrderItem(models.Model):
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="purchase_order_items")
    quantity = models.PositiveIntegerField(null=False, blank=False)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product_name = models.CharField(max_length=100, null=True)

    def save(self, *args, **kwargs):
        if self.product:
            self.product_name = self.product.name
        super(PurchaseOrderItem, self).save(*args, **kwargs)

    def __str__(self):
        return self.product.name
