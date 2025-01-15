from django.contrib import admin
from .models import Category, Income, Expense, EMI, Budget, Alert, Report, UserProfile, UserDetail,ContactUs, NewsletterSubscriber


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'user', 'created_at')
    list_filter = ('category_type', 'created_at')
    search_fields = ('name', 'user__email')

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'amount', 'date', 'created_at')
    list_filter = ('date', 'category')
    search_fields = ('user__email', 'category__name')
    ordering = ('-date',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'amount', 'is_fixed', 'date', 'created_at')
    list_filter = ('is_fixed', 'date', 'category')
    search_fields = ('user__email', 'category__name')
    ordering = ('-date',)

@admin.register(EMI)
class EMIAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'frequency', 'start_date', 'end_date', 'next_payment_date')
    list_filter = ('frequency', 'start_date')
    search_fields = ('user__email',)

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'limit', 'start_date', 'end_date')
    list_filter = ('start_date', 'end_date', 'category')
    search_fields = ('user__email', 'category__name')

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__email', 'message')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'report_type', 'start_date', 'end_date', 'created_at', 'file_path')
    list_filter = ('report_type', 'created_at')
    search_fields = ('user__email', 'report_type')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'budget_limit')
    search_fields = ('user__email',)


@admin.register(UserDetail)
class UserDetailAdmin(admin.ModelAdmin):
    list_display = ['user', 'address', 'date_of_birth', 'budget_limit']


@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'submitted_at')
    search_fields = ('name', 'email')

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')
    search_fields = ('email',)