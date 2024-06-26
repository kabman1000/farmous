from django.contrib import admin
import csv
from django.http import HttpResponse
from .models import Order, OrderItem, InventoryReport, SalesReport, Product
from datetime import datetime
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Sum, Min, F, DecimalField
from decimal import Decimal

admin.site.register(Order)
admin.site.register(OrderItem)


@admin.register(InventoryReport)
class InventoryAdmin(admin.ModelAdmin):
    actions = ["export_as_csv"]

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields if field.name not in ["id"]]

        earliest_date = queryset.order_by('created').values_list('created', flat=True).first()
        latest_date = queryset.order_by('-created').values_list('created', flat=True).first()

        if earliest_date and latest_date:
            formatted_earliest_date = earliest_date.strftime('%Y-%m-%d')
            formatted_latest_date = latest_date.strftime('%Y-%m-%d')
            date_range = f"{formatted_earliest_date} to {formatted_latest_date}"
            formatted_date = formatted_latest_date  # Use the latest date for the filename
        else:
            # Fallback to the current date if no date is found
            formatted_date = datetime.now().strftime('%Y-%m-%d')
            date_range = f"Date: {formatted_date}"

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=inventory_{formatted_date}.csv'
        
        writer = csv.writer(response)

        # Write the date range at the top of the CSV file
        writer.writerow([f"Inventory Report for: {date_range}"])
        writer.writerow([])  # Add an empty row for spacing
        writer.writerow(field_names)  # Write the header row

        for obj in queryset:
            row = [getattr(obj, field) for field in field_names]
            writer.writerow(row)

        return response

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        products = Product.objects.all()

        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=5)  # Last 5 days

        # Collect reports to be created or updated in bulk
        reports_to_create = []
        reports_to_update = []

        for product in products:
            current_date = start_date
            while current_date <= end_date:
                created_datetime = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))

                report, created = InventoryReport.objects.get_or_create(
                    product=product,
                    created=created_datetime,
                    defaults={
                        'days_on_hand': 0,
                        'inventory_on_hand': 0,
                        'quantity_sold': 0,
                    }
                )

                if created:
                    reports_to_create.append(report)
                else:
                    # If the report already exists, add it to the list to update
                    reports_to_update.append(report)
                
                current_date += timedelta(days=1)

        # Bulk create reports
        InventoryReport.objects.bulk_create(reports_to_create, ignore_conflicts=True)

        # Bulk update reports if needed
        if reports_to_update:
            InventoryReport.objects.bulk_update(
                reports_to_update,
                ['days_on_hand', 'inventory_on_hand', 'quantity_sold']
            )

        return InventoryReport.objects.filter(created__gte=start_date)

    
    list_display = ['product','days_on_hand', 'inventory_on_hand', 'quantity_sold', 'created']
    list_per_page = 20  # Ensure pagination
    



@admin.register(SalesReport)
class SalesAdmin(admin.ModelAdmin):
    actions = ["export_as_csv"]

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields if field.name not in [ "order","id"]]

        earliest_date = queryset.order_by('date_created').values_list('date_created', flat=True).first()
        latest_date = queryset.order_by('-date_created').values_list('date_created', flat=True).first()

        if earliest_date and latest_date:
            formatted_earliest_date = earliest_date.strftime('%Y-%m-%d')
            formatted_latest_date = latest_date.strftime('%Y-%m-%d')
            date_range = f"{formatted_earliest_date} to {formatted_latest_date}"
            formatted_date = formatted_latest_date  # Use the latest date for the filename
        else:
            # Fallback to the current date if no date is found
            formatted_date = datetime.now().strftime('%Y-%m-%d')
            date_range = f"Date: {formatted_date}"

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=sales_{formatted_date}.csv'
        
        writer = csv.writer(response)

        # Write the date range at the top of the CSV file
        writer.writerow([f"Sales Report for: {date_range}"])
        writer.writerow([])  # Add an empty row for spacing
        writer.writerow(field_names)  # Write the header row

        for obj in queryset:
            row = [getattr(obj, field) for field in field_names]
            writer.writerow(row)

        return response

    export_as_csv.short_description = "Export Selected"
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        products = Product.objects.all()  # Limit to 50 products

        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=14)  # Last 14 days

        # Collect reports to be created or updated in bulk
        reports_to_create = []
        reports_to_update = []

        for product in products:
            current_date = start_date
            while current_date <= end_date:
                created_datetime = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))

                total_sales = OrderItem.objects.filter(
                    product=product,
                    order__created__date=current_date
                ).aggregate(total=Sum(F('price') * F('quantity'), output_field=DecimalField()))['total'] or Decimal('0.00')
                total_units_sold = OrderItem.objects.filter(
                    product=product,
                    order__created__date=current_date
                ).aggregate(total=Sum('quantity'))['total'] or 0
                number_of_transactions = OrderItem.objects.filter(
                    product=product,
                    order__created__date=current_date
                ).values('order_id').distinct().count()
                average_transaction_value = total_sales / number_of_transactions if number_of_transactions else Decimal('0.00')
                product_price = product.selling_price

                report, created = SalesReport.objects.get_or_create(
                    product=product,
                    date_created=created_datetime,
                    defaults={
                        'product_price': product_price,
                        'total_sales': total_sales,
                        'total_units_sold': total_units_sold,
                        'number_of_transactions': number_of_transactions,
                        'average_transaction_value': average_transaction_value,
                    }
                )

                if created:
                    reports_to_create.append(report)
                else:
                    report.product_price = product_price
                    report.total_sales = total_sales
                    report.total_units_sold = total_units_sold
                    report.number_of_transactions = number_of_transactions
                    report.average_transaction_value = average_transaction_value
                    reports_to_update.append(report)

                current_date += timedelta(days=1)

        # Bulk create reports
        SalesReport.objects.bulk_create(reports_to_create, ignore_conflicts=True)

        # Bulk update reports if needed
        if reports_to_update:
            SalesReport.objects.bulk_update(
                reports_to_update,
                ['product_price', 'total_sales', 'total_units_sold', 'number_of_transactions', 'average_transaction_value']
            )

        return SalesReport.objects.filter(date_created__gte=start_date)

    
    list_display = ['product', 'product_price', 'total_sales', 'total_units_sold', 'number_of_transactions', 'average_transaction_value', 'date_created']
    list_per_page = 20  # Ensure pagination