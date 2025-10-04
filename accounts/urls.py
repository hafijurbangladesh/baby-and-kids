from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .analytics_views import ShopAssistantAnalyticsView, ShopAssistantReportsView

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('customers/', views.CustomerListView.as_view(), name='customer-list'),
    path('customers/add/', views.CustomerCreateView.as_view(), name='customer-add'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer-detail'),
    path('customers/<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer-edit'),
    path('customers/<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer-delete'),
    path('salespersons/', views.SalespersonListView.as_view(), name='salesperson-list'),
    
    # Shop Assistant URLs
    path('shop-assistants/', views.ShopAssistantListView.as_view(), name='shop-assistant-list'),
    path('shop-assistants/add/', views.ShopAssistantCreateView.as_view(), name='shop-assistant-add'),
    path('shop-assistants/<int:pk>/', views.ShopAssistantDetailView.as_view(), name='shop-assistant-detail'),
    path('shop-assistants/<int:pk>/edit/', views.ShopAssistantUpdateView.as_view(), name='shop-assistant-edit'),
    path('shop-assistants/<int:pk>/delete/', views.ShopAssistantDeleteView.as_view(), name='shop-assistant-delete'),
    
    # Shop Assistant Analytics & Reports
    path('shop-assistants/analytics/', ShopAssistantAnalyticsView.as_view(), name='shop-assistant-analytics'),
    path('shop-assistants/reports/', ShopAssistantReportsView.as_view(), name='shop-assistant-reports'),
    
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('api/customer-search/', views.customer_search, name='customer-search'),
    path('api/customer-create/', views.customer_create, name='customer-create'),
    path('api/shop-assistant-search/', views.shop_assistant_search, name='shop-assistant-search'),
]
