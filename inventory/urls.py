from django.urls import path
from .import views

urlpatterns = [
    path('', views.homepage, name='home'),
    path('stores', views.store_list, name='store_list'),
    path('products', views.products, name='products'),
    path('summary', views.store_purchases, name='summary'),
    path('sales-report/store/', views.sales_report_by_store, name='sales_report_by_store'),
    path('stock/report/', views.product_stock_report, name='stock_report'),
    path('supplier-purchase/', views.supplier_purchase_history, name='supplier-purchase'),
    path('sales-report', views.sales_report, name='sales_reports'),
    path('stock_data/', views.stock_data, name='stock'),
    path('products/<int:store_id>/', views.product_list, name='product_list'),
    path('purchase-value/', views.purchase_report, name='purchase_value'),
    path('inventory-value/', views.inventory_value_report, name='inventory_value'),
    path('purchase/<int:store_id>/<int:product_id>/', views.purchase_product, name='purchase_product'),
    path('sell/<int:store_id>/<int:product_id>/', views.sell_product, name='sell_product'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('stores/<int:store_id>/profit_loss/', views.calculate_profit_loss, name='profit_loss'),
    path('add-purchased-product/', views.add_purchased_product, name='add_purchased_product'),
    path('add-sold-product/', views.add_sold_product, name='add_sold_product'),
    path('stock/add/', views.add_stock, name='add_stock'),
    path('stock/update/<int:stock_id>/', views.update_stock, name='update_stock'),
    path('stock/delete/<int:stock_id>/', views.delete_stock, name='delete_stock'),
]