from django.db import models
from authentication.models import User
from django.utils.timezone import now


class Category(models.Model):
    INCOME = 'INCOME'
    EXPENSE = 'EXPENSE'
    CATEGORY_TYPES = [
        (INCOME, 'INCOME'),
        (EXPENSE, 'EXPENSE'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='categories')
    name = models.CharField(max_length=50)
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES, default=INCOME)  # Default to 'Income'
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.category_type})"

    class Meta:
        unique_together = ('user', 'name', 'category_type')


class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='income')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, limit_choices_to={'category_type': 'Income'}, related_name='income')
    description = models.TextField(blank=True, null=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.category.name} - {self.amount}"


class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, limit_choices_to={'category_type': 'Expense'}, related_name='expenses')
    description = models.TextField(blank=True, null=True)
    date = models.DateField()
    is_fixed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.category.name} - {self.amount}"


class EMI(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Completed', 'Completed'),
    ]

    FREQUENCY_CHOICES = [
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('Custom Frequency', 'Custom Frequency'),  # frequency option
        ('Custom Dates', 'Custom Dates')  #custom date option
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emis')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    custom_frequency_days = models.PositiveIntegerField(blank=True, null=True)  # Custom frequency in days
    custom_payment_dates = models.JSONField(blank=True, null=True)  # Custom dates
    description = models.TextField(blank=True, null=True)
    next_payment_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')  
    notified = models.BooleanField(default=False)  # Tracks if user is notified about the EMI

    def __str__(self):
        return f"{self.user.email} - EMI {self.amount} - {self.frequency}"



class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True) 
    limit = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.user.email} - {self.category.name if self.category else 'Overall'} Budget {self.limit}"



class Alert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert for {self.user.email}: {self.message[:30]}"



class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    file_path = models.FileField(upload_to='reports/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for {self.user.email} - {self.report_type}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="userprofile")
    budget_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"Profile of {self.user.email}"



class UserDetail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="details")
    address = models.TextField(blank=True, null=True) 
    date_of_birth = models.DateField(blank=True, null=True) 
    budget_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0.0) 

    def __str__(self):
        return f"Details of {self.user.email}"



# model for implementing the notifications

class Notification(models.Model):
    MESSAGE_TYPE_CHOICES = (
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    message_type = models.CharField(max_length=7, choices=MESSAGE_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  # Track whether the notification is read

    def __str__(self):
        return self.message


from django.db import models

class ContactUs(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.email}"

class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
   