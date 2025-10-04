from django.urls import path
from . import views
from django.views.generic import TemplateView

app_name = 'sales'

urlpatterns = [
    path('', views.SaleListView.as_view(), name='sale-list'),
    path('pos/', views.POSView.as_view(), name='pos'),
    path('test-customer-search/', TemplateView.as_view(template_name='sales/test_customer_search.html'), name='test-customer-search'),
    path('order/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('order/<int:pk>/email/', views.email_receipt, name='email-receipt'),
    path('order/<int:pk>/refund/', views.process_refund, name='process-refund'),
    path('api/complete-sale/', views.complete_sale, name='complete-sale'),
    path('api/product-info/<int:pk>/', views.get_product_info, name='product-info'),
    path('api/search-customers/', views.search_customers, name='search-customers'),
]
