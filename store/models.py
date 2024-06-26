from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse


class ProductManager(models.Manager):
    def get_queryset(self):
        return super(ProductManager, self).get_queryset().filter(in_stock=True)

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_name = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=15)
    address = models.TextField()

    def __str__(self):
        return self.name

class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('store:category_list', args=[self.slug])

class SubCategory(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    categories = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Product(models.Model):
    title = models.CharField(max_length=200,unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='product_creator')
    code = models.CharField(max_length=255, default='')
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, blank=True, null= True)
    description = models.TextField(blank=True, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    products = ProductManager()
    objects = models.Manager()
    created = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(max_length=255)
    in_stock = models.BooleanField(default=True)
    exp_date= models.DateTimeField()
    mfg_date= models.DateTimeField()
    quantity = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Products'
        ordering = ('-created',)

    def get_absolute_url(self):
        return reverse('store:product_detail', args=[self.slug])

    def __str__(self):
        return self.title

    def has_inventory(self):
        return self.quantity > 0 # True or False

    def remove_items_from_inventory(self, count=1, save=True):
        current_inv = self.quantity
        current_inv -= count
        self.quantity = current_inv
        if save == True:
            self.save()
        return self.quantity


class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.PositiveIntegerField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.title} - {self.quantity}"

class InventoryMovement(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_movements')
    quantity = models.IntegerField()
    movement_date = models.DateTimeField(auto_now_add=True)
    movement_type = models.CharField(max_length=20, choices=[('Stock In', 'Stock In'), ('Stock Out', 'Stock Out')])

    def __str__(self):
        return f"{self.movement_type} of {self.quantity} units of {self.product.title} on {self.movement_date}"

    def save(self, *args, **kwargs):
        # Override the save method to update the inventory quantity
        super().save(*args, **kwargs)
        inventory = self.product
        print(inventory)
        if self.movement_type == 'Stock In':
            inventory.quantity += self.quantity
        elif self.movement_type == 'Stock Out':
            inventory.quantity -= self.quantity
        inventory.save()


