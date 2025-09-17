from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('reports/sales/', views.SalesReportView.as_view(), name='sales-report'),
    path('reports/inventory/', views.InventoryReportView.as_view(), name='inventory-report'),
    path('reports/sales/export/', views.export_sales_report, name='sales-report-export'),
    path('reports/inventory/export/', views.export_inventory_report, name='inventory-report-export'),
]
