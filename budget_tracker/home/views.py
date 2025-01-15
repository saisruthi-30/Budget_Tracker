from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Income, Expense, Category, UserProfile, EMI, Budget, Alert, UserDetail, User, Notification, ContactUs, NewsletterSubscriber

from django.db import models
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import date
from django.core.paginator import Paginator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.dateparse import parse_date
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO
from datetime import date, timedelta, datetime
import pandas as pd
import matplotlib.pyplot as plt
import base64
from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models.functions import TruncMonth
from django.db.models import Sum
from django.db.models.signals import post_save
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.http import JsonResponse
from .models import Notification

def home(request):
    return render(request, 'home/home.html')


@login_required
def add_income(request):
    categories = Category.objects.filter(category_type=Category.INCOME)
    if not categories.exists():
        messages.warning(request, "No income categories available. Please create one first.")
        return redirect('category')

    if request.method == 'POST':
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        description = request.POST.get('description')
        category_id = request.POST.get('category')

        if amount and date and description and category_id:
            try:
                selected_category = Category.objects.get(id=category_id)
                Income.objects.create(
                    user=request.user,
                    amount=amount,
                    date=date,
                    description=description,
                    category=selected_category
                )

                  # Add a notification after adding income
               
                notification_message = f"New income of {amount} added under category '{selected_category.name}'."
                Notification.objects.create(
                    user=request.user,
                    message=notification_message,
                    message_type='success'  # Type is set to 'success'
                )

                messages.success(request, "Income added successfully!")
                return redirect('income')
            except Category.DoesNotExist:
                messages.error(request, "Invalid category selected.")
        else:
            messages.error(request, "All fields are required.")
    return render(request, 'home/add_income.html', {'categories': categories})





@login_required
def add_expense(request):
    # Filter expense categories for the user
    categories = Category.objects.filter(user=request.user, category_type=Category.EXPENSE)
    if not categories.exists():
        messages.warning(request, "No Expense categories available. Please create one first.")
        return redirect('category')
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        description = request.POST.get('description')
        category_id = request.POST.get('category')

        # Validate required fields
        if not amount or not date:
            messages.error(request, "Amount and date are required.")
            return redirect('expense')

        # Validate category
        try:
            category = Category.objects.get(
                id=category_id, 
                user=request.user, 
                category_type=Category.EXPENSE
            )
        except Category.DoesNotExist:
            messages.error(request, "Please select a valid expense category.")
            return redirect('expense')

        # Create the expense
        expense = Expense.objects.create(
            user=request.user,
            amount=amount,
            date=date,
            description=description,
            category=category
        )

        # Add a notification after adding expense

        notification_message = f"New expense of {amount} added under category '{category.name}'."
        Notification.objects.create(
            user=request.user,
            message=notification_message,
            message_type='danger'  # Type is set to 'danger'
        )
       
        monitor_budget(Expense, expense, request=request)

        messages.success(request, "Expense added successfully!")
        return redirect('expense')

    return render(request, 'home/add_expense.html', {'categories': categories})


@login_required
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category_type = request.POST.get('category_type')

        if not name or not category_type:
            messages.error(request, "Both category name and type are required.")
            return redirect('category')

        valid_types = [choice[0] for choice in Category.CATEGORY_TYPES]
        if category_type not in valid_types:
            messages.error(request, "Invalid category type.")
            return redirect('category')

        if Category.objects.filter(user=request.user, name=name, category_type=category_type).exists():
            messages.error(request, "Category already exists.")
            return redirect('category')

        Category.objects.create(user=request.user, name=name, category_type=category_type)

        # Add a notification after adding category

        try:
            notification_message = f"New category '{name}' added under '{category_type}'."
            Notification.objects.create(
                user=request.user,
                message=notification_message,
                message_type='info'
            )
            
        except Exception as e:
            print(f"Error creating notification: {e}")

        messages.success(request, "Category added successfully!")
        return redirect('category')

    return render(request, 'home/add_category.html')


@login_required
def dashboard(request):

    now = datetime.now()
    filter_type = request.GET.get('filter_type', 'current_month')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    if filter_type == 'current_month':
        start_date = f"{now.year}-{now.month:02d}-01"
        end_date = f"{now.year}-{now.month:02d}-{now.day:02d}"
    elif filter_type == 'yearly':
        start_date = f"{now.year}-01-01"
        end_date = f"{now.year}-12-31"
    elif filter_type == 'custom':
        if not start_date or not end_date:
            start_date = f"{now.year}-{now.month:02d}-01"
            end_date = f"{now.year}-{now.month:02d}-{now.day:02d}"

    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Query incomes, expenses, and categories
    incomes = Income.objects.filter(user=request.user, date__range=[start_date, end_date])
    expenses = Expense.objects.filter(user=request.user, date__range=[start_date, end_date])
    categories = Category.objects.filter(user=request.user)

    # Calculate totals
    total_income = incomes.aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    balance = total_income - total_expenses

    # Financial summary for line chart (grouped by month)
    income_data = (
        incomes.annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total_income=Sum('amount'))
        .order_by('month')
    )
    expense_data = (
        expenses.annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total_expense=Sum('amount'))
        .order_by('month')
    )
    line_labels = sorted(set([data['month'] for data in income_data] + [data['month'] for data in expense_data]))
    income_dict = {data['month']: data['total_income'] for data in income_data}
    expense_dict = {data['month']: data['total_expense'] for data in expense_data}
    income_data = [income_dict.get(month, 0) for month in line_labels]
    expense_data = [expense_dict.get(month, 0) for month in line_labels]
    balance_data = [i - e for i, e in zip(income_data, expense_data)]

    # Category-wise expenses for bar chart
    category_expense_data = (
        expenses.values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    bar_labels = [entry['category__name'] for entry in category_expense_data]
    bar_data = [float(entry['total']) for entry in category_expense_data]

    # Category-wise income for bar chart
    category_income_data = (
        incomes.values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    income_bar_labels = [entry['category__name'] for entry in category_income_data]
    income_bar_data = [float(entry['total']) for entry in category_income_data]

    # Category-wise budget usage for pie chart
    category_budget_data = []
    for category in categories.filter(category_type='EXPENSE'):
        # Allocated budget
        allocated_budget = Budget.objects.filter(
            user=request.user, category=category, start_date__lte=end_date, end_date__gte=start_date
        ).aggregate(total=Sum('limit'))['total'] or 0
        
        # Used budget
        used_budget = expenses.filter(category=category).aggregate(total=Sum('amount'))['total'] or 0
        category_budget_data.append({
            'category': category.name,
            'allocated_budget': float(allocated_budget),
            'used_budget': float(used_budget),
            'overbudget': float(used_budget - allocated_budget) if used_budget > allocated_budget else None
        })

    # Overall budget progress bar
    overall_budget = Budget.objects.filter(user=request.user, category__isnull=True).aggregate(
        total=Sum('limit'))['total'] or 0
    overall_budget_used = total_expenses
    overall_budget_progress = (overall_budget_used / overall_budget * 100) if overall_budget > 0 else 0

    # Category-wise income for pie chart (for breakdown)
    category_income_data = (
        incomes.values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    pie_labels = [entry['category__name'] for entry in category_income_data]
    pie_data = [float(entry['total']) for entry in category_income_data]

    # Context data
    context = {
        'categories': categories,
        'total_income': float(total_income),
        'total_expenses': float(total_expenses),
        'balance': float(balance),
        'line_labels': [label.strftime('%Y-%m') for label in line_labels],
        'income_data': [float(x) for x in income_data],
        'expense_data': [float(x) for x in expense_data],
        'balance_data': [float(x) for x in balance_data],
        'bar_labels': bar_labels,
        'bar_data': bar_data,
        'income_bar_labels': income_bar_labels,
        'income_bar_data': income_bar_data,
        'category_budget_data': category_budget_data,
        'overall_budget': float(overall_budget),
        'overall_budget_used': float(overall_budget_used),
        'overall_budget_progress': round(overall_budget_progress, 2),
        'pie_labels': pie_labels,
        'pie_data': pie_data,
        'filter_type': filter_type,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
    }

    return render(request, 'home/dashboard.html', context)



@login_required
def generate_report(request):
    period = request.GET.get('period')  # e.g., "current_month", "financial_year", "custom"
    format = request.GET.get('format')  # e.g., "pdf" or "excel"
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    report_type = request.GET.get('report_type', 'expense')  # "expense" or "income"

    # Determine date range
    today = date.today()
    if period == 'current_month':
        start_date = today.replace(day=1)
        end_date = today
    elif period == 'financial_year':
        # financial year starts April 1
        start_date = today.replace(month=4, day=1) if today.month >= 4 else today.replace(year=today.year - 1, month=4, day=1)
        end_date = today
    elif period == 'custom' and start_date and end_date:
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)
    else:
        # Default to current month if no valid period is provided
        start_date = today.replace(day=1)
        end_date = today

    # Fetch expenses or income within the date range
    if report_type == 'expense':
        data = Expense.objects.filter(user=request.user, date__range=[start_date, end_date])
        filename = f"expense_report_{start_date}_{end_date}"
    else:
        data = Income.objects.filter(user=request.user, date__range=[start_date, end_date])
        filename = f"income_report_{start_date}_{end_date}"

    if format == 'pdf':
        # Generate PDF report
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)

        # Generate the table for the report
        table_data = [["Category", "Amount", "Date", "Description"]]
        for entry in data:
            table_data.append([entry.category.name, f"₹{entry.amount}", entry.date, entry.description or ""])

        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        elements = []
        styles = getSampleStyleSheet()
        elements.append(Paragraph(f"{report_type.capitalize()} Report", styles['Title']))
        elements.append(Paragraph(f"Date Range: {start_date} to {end_date}", styles['Normal']))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        response.write(buffer.read())
        return response

    elif format == 'excel':
        # Generate Excel report
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'

        df = pd.DataFrame(list(data.values('category__name', 'amount', 'date', 'description')))
        df.to_excel(response, index=False)
        return response

    return render(request, 'home/generate_report.html', {
        'start_date': start_date,
        'end_date': end_date,
        'data': data,
        'report_type': report_type,
    })


@login_required
def update_income(request, pk):
   
    income = get_object_or_404(Income, id=pk, user=request.user)
    categories = Category.objects.filter(user=request.user, category_type=Category.INCOME)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        description = request.POST.get('description')
        category_id = request.POST.get('category')

        if not amount or not date or not category_id:
            messages.error(request, "All fields are required.")
            return redirect('update_income', pk=pk)

        try:
            category = Category.objects.get(id=category_id, user=request.user, category_type=Category.INCOME)
            income.amount = amount
            income.date = date
            income.description = description
            income.category = category
            income.save()  
            
            notification_message = f"Income updated to {amount} under category '{category.name}'."
            Notification.objects.create(
                user=request.user,
                message=notification_message,
                message_type='info'
            )

            messages.success(request, "Income updated successfully.")
            return redirect('dashboard')
        except Category.DoesNotExist:
            messages.error(request, "Invalid category.")
            return redirect('update_income', pk=pk)

    return render(request, 'home/update_income.html', {'income': income, 'categories': categories})

@login_required
def update_expense(request, pk):
    
    expense = get_object_or_404(Expense, id=pk, user=request.user)
    categories = Category.objects.filter(user=request.user, category_type=Category.EXPENSE)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        description = request.POST.get('description')
        category_id = request.POST.get('category')

        if not amount or not date or not category_id:
            messages.error(request, "All fields are required.")
            return redirect('update_expense', pk=pk)

        try:
            category = Category.objects.get(id=category_id, user=request.user, category_type=Category.EXPENSE)
            expense.amount = amount
            expense.date = date
            expense.description = description
            expense.category = category
            expense.save()  
            messages.success(request, "Expense updated successfully.")

            notification_message = f"Expense updated to {amount} under category '{category.name}'." 
            Notification.objects.create(
                user=request.user,
                message=notification_message,
                message_type='info'
            )

            return redirect('dashboard')
        except Category.DoesNotExist:
            messages.error(request, "Invalid category.")
            return redirect('update_expense', pk=pk)

    return render(request, 'home/update_expense.html', {'expense': expense, 'categories': categories})

@login_required
def delete_income(request, pk):
    if request.method == 'POST':  
        income = get_object_or_404(Income, id=pk, user=request.user)
        income.delete()

        notification_message = f"Income deleted for amount {income.amount} under category '{income.category.name}'."
        Notification.objects.create(
            user=request.user,
            message=notification_message,
            message_type='danger'
        )

        return HttpResponse(status=200)  
    return HttpResponse(status=405) 


@login_required
def delete_expense(request, pk):
    if request.method == 'POST': 
        expense = get_object_or_404(Expense, id=pk, user=request.user)
        expense.delete()
        notification_message = f"Expense deleted for amount {expense.amount} under category '{expense.category.name}'."
        Notification.objects.create(
            user=request.user,
            message=notification_message,
            message_type='danger'
        )
        return HttpResponse(status=200) 
    return HttpResponse(status=405) 




@login_required
def add_emi(request):
    if request.method == 'POST':
       
        amount = request.POST.get('amount')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        frequency = request.POST.get('frequency')
        description = request.POST.get('description', '')
        custom_dates = request.POST.getlist('custom_dates') 
        custom_frequency_days = request.POST.get('custom_frequency_days') 

      
        if not amount or not start_date or not end_date or not frequency:
            messages.error(request, "All fields are required.")
            return redirect('add_emi')

        try:
            
            emi = EMI.objects.create(
                user=request.user,
                amount=float(amount),
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                description=description,
                next_payment_date=start_date,
                custom_payment_dates=custom_dates if frequency == 'Custom Dates' else None,
                custom_frequency_days=int(custom_frequency_days) if frequency == 'Custom Frequency' else None
            )

            notification_message = f"New EMI of {amount} created successfully!"
            Notification.objects.create(
                user=request.user,
                message=notification_message,
                message_type='success'
            )

            messages.success(request, f"EMI of {amount} created successfully!")
            return redirect('view_emis')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

    return render(request, 'home/add_emi.html')



@login_required

def view_emis(request):
    emis = EMI.objects.filter(user=request.user, status='Active').order_by('next_payment_date')

    return render(request, 'home/view_emis.html', {'emis': emis})



from django.shortcuts import get_object_or_404

@login_required
def edit_emi(request, emi_id):
    emi = get_object_or_404(EMI, id=emi_id, user=request.user)

    if request.method == 'POST':
        # Gather form data
        amount = request.POST.get('amount')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        frequency = request.POST.get('frequency')
        description = request.POST.get('description', '')
        custom_dates = request.POST.getlist('custom_dates') 
        custom_frequency_days = request.POST.get('custom_frequency_days')  # Custom frequency days

        
        if not amount or not start_date or not end_date or not frequency:
            messages.error(request, "All fields are required.")
            return redirect('edit_emi', emi_id=emi_id)

        try:
           
            emi.amount = float(amount)
            emi.start_date = start_date
            emi.end_date = end_date
            emi.frequency = frequency
            emi.description = description
            emi.custom_payment_dates = custom_dates if frequency == 'Custom Dates' else None
            emi.custom_frequency_days = int(custom_frequency_days) if frequency == 'Custom Frequency' else None
            emi.next_payment_date = start_date  # Reset the next payment date
            emi.save()

            notification_message = f"EMI updated for {amount} successfully!"
            Notification.objects.create(
                user=request.user,
                message=notification_message,
                message_type='info'
            )

            messages.success(request, "EMI updated successfully!")
            return redirect('view_emis')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('edit_emi', emi_id=emi_id)

    return render(request, 'home/edit_emi.html', {'emi': emi})

@login_required
def delete_emi(request, emi_id):
    emi = get_object_or_404(EMI, id=emi_id, user=request.user)

    if request.method == 'POST':
        emi.delete()
        notification_message = f"EMI deleted for {emi.amount} '."
        Notification.objects.create(
            user=request.user,
            message=notification_message,
            message_type='danger'
        )
        messages.success(request, "EMI deleted successfully!")
        return redirect('view_emis')

    return render(request, 'home/delete_emi.html', {'emi': emi})



@login_required
def view_incomes(request):
    
    incomes = Income.objects.filter(user=request.user).order_by('-date')

    
    category_filter = request.GET.get('category')
    if category_filter:
        incomes = incomes.filter(category__id=category_filter)

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        incomes = incomes.filter(date__gte=start_date)
    if end_date:
        incomes = incomes.filter(date__lte=end_date)

    
    paginator = Paginator(incomes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    
    categories = Category.objects.filter(user=request.user, category_type=Category.INCOME)

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'home/view_incomes.html', context)


@login_required
def view_expenses(request):
    
    expenses = Expense.objects.filter(user=request.user).order_by('-date')

    
    category_filter = request.GET.get('category')
    if category_filter:
        expenses = expenses.filter(category__id=category_filter)

    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        expenses = expenses.filter(date__gte=start_date)
    if end_date:
        expenses = expenses.filter(date__lte=end_date)

    
    paginator = Paginator(expenses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    
    categories = Category.objects.filter(user=request.user, category_type=Category.EXPENSE)

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'home/view_expenses.html', context)


@login_required
def view_completed_emis(request):
    completed_emis = EMI.objects.filter(user=request.user, status='Completed').order_by('-end_date')
    return render(request, 'home/view_completed_emis.html', {'completed_emis': completed_emis})
@login_required
def set_budget(request):
    from datetime import datetime
    from calendar import monthrange

    # Get the current month's start and end dates
    today = datetime.now()
    start_date = today.replace(day=1).date()
    end_date = today.replace(day=monthrange(today.year, today.month)[1]).date()

    # Get categories for the dropdown
    categories = Category.objects.filter(user=request.user, category_type='EXPENSE')  # Expense categories only

    if request.method == "POST":
        category_id = request.POST.get('category')
        limit = request.POST.get('limit')

        if not limit:
            messages.error(request, "Budget limit is required.")
            return render(request, 'home/update_budget.html', {
                'categories': categories,
                'current_month': today.strftime('%B %Y'),
            })

        # Handle overall budget
        if category_id == "overall":
            existing_budget = Budget.objects.filter(
                user=request.user, category=None, start_date=start_date, end_date=end_date
            ).first()
            if existing_budget:
                existing_budget.limit = limit
                existing_budget.save()

                notification_message = f"Overall budget updated to {limit} successfully!"
                Notification.objects.create(
                    user=request.user,
                    message=notification_message,
                    message_type='info'
                )

                messages.success(request, "Overall budget updated successfully!")
            else:
                Budget.objects.create(
                    user=request.user,
                    category=None,  # Overall budget
                    limit=limit,
                    start_date=start_date,
                    end_date=end_date
                )
                notification_message = f"Overall budget updated to {limit} successfully!"
                Notification.objects.create(
                    user=request.user,
                    message=notification_message,
                    message_type='info'
                )
                messages.success(request, "Overall budget set successfully!")
        else:
            # Handle category-specific budget
            category = Category.objects.get(id=category_id)
            existing_budget = Budget.objects.filter(
                user=request.user, category=category, start_date=start_date, end_date=end_date
            ).first()
            if existing_budget:
                existing_budget.limit = limit
                existing_budget.save()
                notification_message = f"Budget for {category.name} updated to {limit} successfully!"
                Notification.objects.create(
                    user=request.user,
                    message=notification_message,
                    message_type='info'
                )
                messages.success(request, f"Budget for {category.name} updated successfully!")
            else:
                Budget.objects.create(
                    user=request.user,
                    category=category,
                    limit=limit,
                    start_date=start_date,
                    end_date=end_date
                )
                notification_message = f"Budget for {category.name} set to {limit} successfully!"
                Notification.objects.create(
                    user=request.user,
                    message=notification_message,
                    message_type='info'
                )
                messages.success(request, f"Budget for {category.name} set successfully!")

        return redirect('budget')

    return render(request, 'home/update_budget.html', {
        'categories': categories,
        'current_month': today.strftime('%B %Y'),  # e.g., "December 2024"
    })


@receiver(post_save, sender=Expense)
def monitor_budget(sender, instance, **kwargs):
    user = instance.user
    total_expenses = user.expenses.aggregate(models.Sum('amount'))['amount__sum'] or 0

    # Check overall budget
    overall_budget = Budget.objects.filter(user=user, category=None).first()
    if overall_budget and total_expenses > overall_budget.limit:
        Alert.objects.create(
            user=user,
            message=f"Overall spending exceeded! You have spent ₹{total_expenses}, exceeding the limit of ₹{overall_budget.limit}."
        )

        # Send email alert
        send_mail(
            'Budget Alert: Overall Spending Exceeded',
            f"Dear {user.name},\n\n"
            f"You have exceeded your overall budget for this month.\n\n"
            f"Total Expenses: ₹{total_expenses}\n"
            f"Budget Limit: ₹{overall_budget.limit}\n\n"
            f"Please review your spending to stay within your budget.",
            'insanehack007@gmail.com',
            [user.email],
            fail_silently=False,
        )

    # Check category-specific budgets
    category_budget = Budget.objects.filter(user=user, category=instance.category).first()
    category_expenses = instance.category.expenses.filter(user=user).aggregate(models.Sum('amount'))['amount__sum'] or 0
    if category_budget and category_expenses > category_budget.limit:
        Alert.objects.create(
            user=user,
            message=f"Budget for {instance.category.name} exceeded! Spent ₹{category_expenses}, limit was ₹{category_budget.limit}."
        )

        # Send email alert
        send_mail(
            f"Budget Alert: {instance.category.name} Spending Exceeded",
            f"Dear {user.name},\n\n"
            f"You have exceeded your budget for the '{instance.category.name}' category.\n\n"
            f"Total Expenses for {instance.category.name}: ₹{category_expenses}\n"
            f"Budget Limit: ₹{category_budget.limit}\n\n"
            f"Please review your spending in this category to stay within your budget.",
            'insanehack007@gmail.com',
            [user.email],
            fail_silently=False,
        )



@login_required
def manage_budget(request):
    from datetime import datetime
    from calendar import monthrange

    # Get the current month's start and end dates
    today = datetime.now()
    start_date = today.replace(day=1).date()
    end_date = today.replace(day=monthrange(today.year, today.month)[1]).date()

    # Retrieve all budgets for the user
    budgets = Budget.objects.filter(user=request.user)

    # Handle budget deletion
    if request.method == "POST" and "delete_budget" in request.POST:
        budget_id = request.POST.get("delete_budget")
        budget = Budget.objects.filter(id=budget_id, user=request.user).first()
        if budget:
            budget.delete()

            notification_message = f"Budget for {budget.category.name if budget.category else 'Overall'} deleted successfully!"
            Notification.objects.create(
                user=request.user,
                message=notification_message,
                message_type='danger'
            )

            messages.success(request, "Budget deleted successfully!")
        else:
            messages.error(request, "Budget not found or you do not have permission to delete it.")
        return redirect('manage_budget')

    context = {
        'budgets': budgets,
        'current_month': today.strftime('%B %Y'),  # Example: "December 2024"
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'home/manage_budget.html', context)

@login_required
def edit_budget(request, budget_id):
    budget = Budget.objects.filter(id=budget_id, user=request.user).first()

    if not budget:
        messages.error(request, "Budget not found.")
        

    if request.method == "POST":
        limit = request.POST.get('limit')
        if not limit:
            messages.error(request, "Budget limit is required.")
        else:
            budget.limit = limit
            budget.save()
            notification_message = f"Budget for {budget.category.name if budget.category else 'Overall'} updated successfully!"
            Notification.objects.create(
                user=request.user,
                message=notification_message,
                message_type='info'
            )
            messages.success(request, f"Budget for {budget.category.name if budget.category else 'Overall'} updated successfully!")
            

    return render(request, 'home/edit_budget.html', {'budget': budget})




# viewing and updating user detials 

@receiver(post_save, sender=User)
def create_user_detail(sender, instance, created, **kwargs):
    if created:
        UserDetail.objects.create(user=instance)

@login_required

def view_profile(request):
    """Display the user's additional details."""
    user_detail, created = UserDetail.objects.get_or_create(user=request.user)
    return render(request, 'home/view_profile.html', {'user_detail': user_detail})






@login_required
def update_profile(request):
    """Allow the user to update their additional details."""
    user_detail, created = UserDetail.objects.get_or_create(user=request.user)

    if request.method == "POST":
        # Capture data from POST request
        name = request.POST.get('name')  # User's name
        address = request.POST.get('address')  # Address field
        date_of_birth = request.POST.get('date_of_birth')  # Date of birth

        # Update the user's name if provided
        if name and name != request.user.name:
            request.user.name = name
            request.user.save()  # Save the User instance

        # Update UserDetail fields if provided
        if address and address != user_detail.address:
            user_detail.address = address
        
        if date_of_birth and date_of_birth != str(user_detail.date_of_birth):
            try:
                user_detail.date_of_birth = date_of_birth
            except ValueError:
                messages.error(request, "Invalid date of birth format.")
        
        # Save the UserDetail instance if any changes are made
        user_detail.save()

        notification_message = "Profile updated successfully!"
        Notification.objects.create(
            user=request.user,
            message=notification_message,
            message_type='info'
        )
        
        
        messages.success(request, "Profile updated successfully!")
        return redirect('view_profile')

    return render(request, 'home/update_profile.html', {'user_detail': user_detail})



# notifications functionality 

def fetch_notifications(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5]
    notification_count = notifications.count()

    # Prepare data to return
    notifications_data = [{
        'message': notification.message,
        'message_type': notification.message_type,
        'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    } for notification in notifications]

    return JsonResponse({
        'notifications': notifications_data,
        'notification_count': notification_count
    })





def mark_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})


# Contact Us View
def contact_us(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Save data to the ContactUs model
        ContactUs.objects.create(name=name, email=email, message=message)
        messages.success(request, 'Your message has been sent successfully!')
        return redirect('home') 

    return redirect('home')

# Newsletter View
def newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('newsletter_email')

        # Save email to the NewsletterSubscriber model
        if not NewsletterSubscriber.objects.filter(email=email).exists():
            NewsletterSubscriber.objects.create(email=email)
            messages.success(request, 'You have been subscribed to our newsletter!')
        else:
            messages.info(request, 'You are already subscribed to our newsletter.')
        
        return redirect('home')  
    return redirect('home')



from django.core.mail import send_mail

def send_upcoming_emi_email(user, emi):
    """Send an email notification to the user about an upcoming EMI payment."""
    subject = f"Upcoming EMI Payment Reminder: {emi.description}"
    message = f"""
Hi {user.name},

This is a reminder for your upcoming EMI payment.

Details:
- Amount: {emi.amount}
- Next Payment Date: {emi.next_payment_date}
- Description: {emi.description}

Please ensure that the payment is made on time.

Thank you for using our service!

Best regards,
Your Budget Tracker Team
"""
    recipient_list = [user.email]
    try:
        send_mail(subject, message, 'your_email@example.com', recipient_list, fail_silently=False)
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False
