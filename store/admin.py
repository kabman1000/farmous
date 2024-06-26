from django.contrib import admin
from .models import ProductCategory, Product, SubCategory,Inventory,InventoryMovement, Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name','contact_name','contact_phone']


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity']

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity','movement_date','movement_type']


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'code','cost_price','selling_price',
                    'in_stock', 'created',]
    list_filter = ['in_stock']
    list_editable = ['selling_price', 'in_stock',]
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['code']


@admin.register(SubCategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display=['name','categories']

