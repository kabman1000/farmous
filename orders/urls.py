from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('add/', views.add, name='add'),

    #path('<slug:slug>', views.sale_orders, name='sales'),
    path('sales/', views.sales, name='sales'),
    path('dash/', views.dash, name='dash'),
    path('customers/', views.customer_rel, name='customer-rel'),
    #path('generateinvoice/<int:pk>/', views.GenerateInvoice.as_view(), name = 'generateinvoice')
]