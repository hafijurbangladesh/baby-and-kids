from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product-list'),
    path('product/add/', views.ProductCreateView.as_view(), name='product-add'),
    path('product/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('product/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product-edit'),
    path('product/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product-delete'),
    path('product/<int:pk>/update-stock/', views.update_stock, name='update-stock'),
    path('low-stock/', views.LowStockListView.as_view(), name='low-stock'),
    path('api/product-search/', views.product_search, name='product-search'),
    path('api/recent-products/', views.recent_products, name='recent-products'),
    path('api/subcategories/', views.get_subcategories, name='get-subcategories'),
    path('api/category-chain/<int:category_id>/', views.get_category_chain, name='get-category-chain'),
]
