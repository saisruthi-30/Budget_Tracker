from django.urls import path
from . import views

urlpatterns = [
  path('', views.home, name='home'), 
  path('income', views.add_income, name='income'), 
  path('expense/', views.add_expense, name='expense'), 
  path('category/', views.add_category, name='category'), 
  path('dashboard/', views.dashboard, name='dashboard'), 
  path('budget/', views.set_budget, name='budget'),
  path('generate-report/', views.generate_report, name='generate_report'),
  path('update-income/<int:pk>/', views.update_income, name='update_income'),
  path('update-expense/<int:pk>/', views.update_expense, name='update_expense'),
  path('delete-income/<int:pk>/', views.delete_income, name='delete_income'),
  path('delete-expense/<int:pk>/', views.delete_expense, name='delete_expense'),
  path('emis/add/', views.add_emi, name='add_emi'),
  path('emis/', views.view_emis, name='view_emis'),
  path('emis/edit/<int:emi_id>/', views.edit_emi, name='edit_emi'),
  path('emis/delete/<int:emi_id>/', views.delete_emi, name='delete_emi'),
  path('completed-emis/', views.view_completed_emis, name='view_completed_emis'),
  path('incomes_entries/', views.view_incomes, name='view_incomes'),
  path('expenses_entries/', views.view_expenses, name='view_expenses'),
  path('manage_budget/', views.manage_budget, name='manage_budget'),
  path('edit_budget/<int:budget_id>/', views.edit_budget, name='edit_budget'),
  path('generate-report/', views.generate_report, name='generate_report'),
  path('profile/', views.view_profile, name='view_profile'),
  path('profile/update/', views.update_profile, name='update_profile'),

  path('fetch-notifications/', views.fetch_notifications, name='fetch_notifications'),
  path('mark-notifications-read/', views.mark_notifications_read, name='mark_notifications_read'),

  path('contact-us/', views.contact_us, name='contact_us'),
  path('newsletter/', views.newsletter, name='newsletter'),
]
