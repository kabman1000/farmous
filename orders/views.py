from django.http.response import JsonResponse
from django.shortcuts import render
from django.views.generic import View
import sys
from django.contrib import messages
# for generating pdf invoice
from django.utils import timezone
from datetime import datetime
from django.shortcuts import get_object_or_404
from .forms import StockHistorySearchForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Sum, Avg
from django.db.models.functions import ExtractYear, ExtractMonth
from django.http import JsonResponse
from basket.basket import Basket
from store.models import Product,InventoryMovement
from .models import Order, OrderItem, InventoryReport, SalesReport


def payment_confirmation(order_number):
    Order.objects.filter(order_number=order_number).update(billing_status=True)


def add(request):
    basket = Basket(request)
    if request.POST.get('action') == 'post':

        order_number = request.POST.get('order_number')
        user_id = request.user.id
        baskettotal = basket.get_total_price()
        full_name = request.POST.get('cusName')
        phone = request.POST.get('phone_num')
        payment_method = request.POST.get('payment_method')

        momo = payment_method == 'momo'
        cash = payment_method == 'cash'
        card = payment_method == 'card'
        # Check if order exists
        if Order.objects.filter(order_number=order_number).exists():
            
            pass
        else:
            order = Order.objects.create(user_id=user_id, full_name=full_name, phone=phone,total_paid=baskettotal, order_number=order_number, momo=momo, cash=cash, card = card)
            payment_confirmation(order_number)
            order_id = order.pk
            print(order_id)

            
            for item in basket:
                quant = item['qty']
                product_id = item['product'].id
                inv = Product.objects.get(id=product_id)
                if inv.has_inventory():
                    inv.remove_items_from_inventory(count=quant)
                    InventoryMovement.objects.create(
                        product=inv,
                        quantity=quant,
                        movement_type='Stock Out'
                    )
                    invo = inv.quantity
                    OrderItem.objects.create(order_id=order_id, product=item['product'], price=item['price'], quantity=item['qty'],inventory=invo)
                    order_date = datetime.now().date()

                    # Retrieve inventory reports for the current product and date
                    inventory_reports = InventoryReport.objects.filter(product=inv, created__date=order_date)

                    if not inventory_reports.exists():
                        # If no inventory reports exist for the current date, create a new one
                        inventory_report = InventoryReport.objects.create(product=inv, created=timezone.now())
                        inventory_reports = [inventory_report]

                    # Update all matching inventory reports
                    for inventory_report in inventory_reports:
                        inventory_report.days_on_hand = inventory_report.calculate_days_on_hand()
                        inventory_report.inventory_on_hand = inv.quantity
                        inventory_report.update_inventory_on_hand = inv.quantity  # Assuming this is the correct field to update
                        inventory_report.amount_sold = inventory_report.calculate_amount_sold()
                        inventory_report.save()

                    order_date = datetime.now().date()

# Retrieve sales reports for the current product and date
                    sales_reports = SalesReport.objects.filter(product=inv, date_created__date=order_date)

                    if not sales_reports.exists():
                        # If no sales reports exist for the current date, create a new one
                        sales_report = SalesReport.objects.create(product=inv, date_created=timezone.now())
                        sales_reports = [sales_report]

                    # Update all matching sales reports
                    for sales_report in sales_reports:
                        sales_report.total_sales = sales_report.calculate_total_sales()
                        sales_report.total_units_sold = sales_report.calculate_total_units_sold()
                        sales_report.number_of_transactions = sales_report.calculate_number_of_transactions()
                        sales_report.average_transaction_value = sales_report.calculate_average_transaction_value()
                        sales_report.save()
                else:
                    messages.error(request, f'{inv.name} is out of stock')

        response = JsonResponse({'success': 'Return something'})
        return response


def user_orders(request):
    user_id = request.user.id
    orders = Order.objects.filter(user_id=user_id).filter(billing_status=True)[:50]
    return orders

@login_required
def sales(request):
    user_id = request.user.id
    sales = Order.objects.filter(user_id=user_id).filter(billing_status=True)[:50]
    form = StockHistorySearchForm(request.POST or None)
    total = sum([sale.total_paid for sale in sales])
    if request.method == 'POST':
        sales = Order.objects.filter(user_id=user_id).filter(billing_status=True).filter(created__range=[form['start_date'].value(),form['end_date'].value()])
        total = sum([sale.total_paid for sale in sales])
    return render(request,
                  'account/user/sales.html', {'sales':sales, 'form':form, 'total':total})

def dash(request):
    orders = Order.objects.all()
    order_items = OrderItem.objects.all()
    return render(request,
                  'account/user/dashmoard.html', {'order_items':order_items, 'orders':orders})

def customer_rel(request):
    orders = Order.objects.exclude(full_name="").exclude(phone="").exclude(full_name="cust").annotate(full_name_count=Count('full_name')).filter(full_name_count=1)
    return render(request,
                  'account/user/customers.html', {'orders':orders})