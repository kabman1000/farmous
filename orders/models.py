from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone
from store.models import Product
from django.db.models import F, Sum
from django.conf import settings
from django.contrib.auth.models import User



class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='order_user')
    full_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=100)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2)
    billing_status = models.BooleanField(default=False)
    order_number = models.AutoField(primary_key=True)
    cash = models.BooleanField(default=False)
    momo = models.BooleanField(default=False)
    card = models.BooleanField(default=False)
    
    def __str__(self):
        return str(self.created)

    class Meta:
        ordering = ('-created',)

        

class OrderItem(models.Model):
    order = models.ForeignKey(Order,
                              related_name='items',
                              on_delete=models.CASCADE,
                              null= True)
    product = models.ForeignKey(Product,
                                related_name='order_items',
                                on_delete=models.SET_NULL,
                                null= True,
                                to_field='title')
    price = models.DecimalField(max_digits=6, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    inventory = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.id)
    
    @property
    def total_cost(self):
        return self.quantity * self.price



class SalesReport(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_units_sold = models.PositiveIntegerField(default=0)
    number_of_transactions = models.PositiveIntegerField(default=0)
    average_transaction_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='sales_reports', null=True)
    date_created = models.DateTimeField(default=timezone.now)

    def calculate_product_price(self):
        return self.product.selling_price

    def calculate_total_sales(self):
        total_sales = self.product.order_items.filter(order__created__date=self.date_created.date()).aggregate(total=Sum(F('price') * F('quantity')))['total']
        return total_sales if total_sales else Decimal('0.00')

    def calculate_total_units_sold(self):
        total_units_sold = self.product.order_items.filter(order__created__date=self.date_created.date()).aggregate(total=Sum('quantity'))['total']
        return total_units_sold if total_units_sold else 0

    def calculate_number_of_transactions(self):
        number_of_transactions = self.product.order_items.filter(order__created__date=self.date_created.date()).values('order_id').distinct().count()
        return number_of_transactions

    def calculate_average_transaction_value(self):
        if self.number_of_transactions > 0:
            return self.total_sales / Decimal(self.number_of_transactions)
        return Decimal('0.00')

    def save(self, *args, **kwargs):
        self.total_sales = self.calculate_total_sales()
        self.product_price = self.calculate_product_price()
        self.total_units_sold = self.calculate_total_units_sold()
        self.number_of_transactions = self.calculate_number_of_transactions()
        self.average_transaction_value = self.calculate_average_transaction_value()
        super().save(*args, **kwargs)





class InventoryReport(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    days_on_hand = models.PositiveIntegerField(default=0)
    inventory_on_hand = models.PositiveIntegerField(default=0)
    quantity_sold = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(default=timezone.now)

    def calculate_days_on_hand(self):
    # Calculate days on hand based on last order date
        if self.product.created:
            days_on_hand = (timezone.now() - self.product.created).days
            return days_on_hand
        return 0

    def calculate_inventory_on_hand(self):
        # Calculate inventory on hand
        return self.product.quantity

    def calculate_amount_sold(self):
        # Calculate total amount sold
        total_quantity_sold = self.product.order_items.filter(order__created__date=self.created.date()).aggregate(total=Sum('quantity'))['total']
        return total_quantity_sold if total_quantity_sold else 0

    def save(self, *args, **kwargs):
        self.days_on_hand = self.calculate_days_on_hand()
        self.inventory_on_hand = self.calculate_inventory_on_hand()
        self.quantity_sold = self.calculate_amount_sold()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Inventory Report for {self.product.title}"
