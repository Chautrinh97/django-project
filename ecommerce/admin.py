from django.contrib import admin
from django.utils.html import format_html
from .models import *
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce
from datetime import datetime


# class CustomerAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name', 'phone_number', 'email', 'shipping_address',)
#     fields = ('id', 'name', 'phone_number', 'email', 'shipping_address',)
#     list_display_links = ('id', 'name',)
#     readonly_fields = [f.name for f in Customer._meta.fields]
#     list_per_page = 15
class CustomerAdmin(admin.ModelAdmin):
    verbose_name = 'Customer'
    verbose_name_plural = 'Customers'
    list_display = ('name', 'email', 'phone_number', 'shipping_address', 'is_verify')
    search_fields = ('name', 'email', 'phone_number',)
    fields = ('name', 'email', 'shipping_address', 'is_verify')
    readonly_fields = ('name', 'email', 'shipping_address', 'is_verify')
    list_per_page = 15

    def has_add_permission(self, request):
        return False


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('preview',)

    def preview(self, obj):
        try:
            return format_html('<img src="{}" width="100" height="100" />'.format(obj.image.url))
        except:
            format_html('<img src="{}" width="10" height="10" />'.format(""))

    preview.allow_tags = True


class ProductAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'price', 'brand', 'pQuantity', 'is_active', 'is_feature', 'created_at',
                    'updated_at']
    fields = ['name', 'category', 'brand', 'price', 'description', 'tech_param', 'is_active', 'is_feature']
    list_display_links = ['name', 'product']
    list_editable = ['price', 'is_active', 'is_feature']
    list_filter = ['brand', 'category', 'category__type', 'is_active']
    search_fields = ['name', 'brand__name', 'category__name', 'category__type__name']
    ordering = ['category__name', 'brand__name', 'is_active']
    list_per_page = 20
    inlines = [ProductImageInline]

    def product(self, obj):
        if obj.images.first():
            return format_html('<img src="{}" width="100" height="100" />'.format(obj.images.first().imageURL))

    product.allow_tags = True

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _quantity=Coalesce(Sum('importorderitem__quantity'), 0) - Coalesce(Sum('purchaseorderitem__quantity'), 0)
        )
        return queryset

    def pQuantity(self, obj):
        return obj._quantity

    pQuantity.allow_tags = True
    pQuantity.admin_order_field = '_quantity'


class InstrumentTypeAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('id', 'name')
    list_editable = ('name',)
    list_per_page = 20
    fields = ('name',)


class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('name', 'type')
    list_display = ('id', 'name', 'type', 'display_home')
    list_filter = ('type',)
    list_editable = ('name', 'type', 'display_home')
    ordering = ('name', 'display_home')
    fields = ('name', 'type', 'display_home')
    list_per_page = 20


class BrandAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('id', 'image_tag', 'name',)
    list_display_links = ('id', 'image_tag')
    list_editable = ('name',)
    ordering = ('name',)
    fields = ('name', 'image')
    list_per_page = 15

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="150" height="100" />'.format(obj.image.url))

    image_tag.allow_tags = 'Image'


# Register your models here.
class SupplierAdmin(admin.ModelAdmin):
    search_fields = ('name', 'phone_number', 'email', 'address')
    list_display = ('id', 'name', 'phone_number', 'email', 'address')
    list_editable = ('name', 'phone_number', 'email')
    ordering = ('name',)
    list_per_page = 20


class ImportOrderItemInline(admin.TabularInline):
    model = ImportOrderItem
    extra = 1
    readonly_fields = ('product_name', 'preview')

    def preview(self, obj):
        if obj.product.images.first():
            return format_html('<img src="{}" width="100" height="100" />'.format(obj.product.images.first().imageURL))

    preview.allow_tags = True


class ImportOrderAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ('id', 'total_price', 'created_at', 'updated_at',)
    list_display_links = ('id', 'total_price',)
    inlines = [ImportOrderItemInline]
    fields = ('supplier',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(total_price=Sum(F('import_order_items__quantity') * F('import_order_items__price')))
        return queryset

    def total_price(self, obj):
        return obj.total_price

    total_price.admin_order_field = 'total_price'
    total_price.short_description = 'Total price'


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ('preview', 'product_name', 'quantity', 'price',)
    readonly_fields = ('preview', 'product', 'product_name', 'quantity', 'price')

    def preview(self, obj):
        if obj.product:
            return format_html('<img src="{}" width="100" height = "100"/>'.format(obj.product.images.first().imageURL))

    preview.allow_tags = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class PurchaseOrderAdmin(admin.ModelAdmin):
    inlines = [PurchaseOrderItemInline]
    fields = (
        'customer_name', 'customer_phone', 'receiver_name', 'receiver_phone', 'ordered_time', 'confirmed_time',
        'shipped_time', 'status'
    )
    readonly_fields = (
        'customer_name', 'customer_phone', 'receiver_name', 'receiver_phone', 'ordered_time', 'confirmed_time',
        'shipped_time',
    )
    list_display = ('id', 'customer_name', 'ordered_time', 'confirmed_time', 'shipped_time', 'status')
    list_per_page = 20

    def has_add_permission(self, request):
        return False


admin.site.register(Customer, CustomerAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(InstrumentType, InstrumentTypeAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(ImportOrder, ImportOrderAdmin)
admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
