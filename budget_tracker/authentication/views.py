from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model

# Get the custom User model
User = get_user_model()

def register_page(request):
    if request.method == 'POST':
        # Retrieve form data
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('confirm_password')
        
        # Check if passwords match
        if password == password_confirm:
            try:
                # Create the new user
                user = User.objects.create_user(
                    email=email, 
                    password=password, 
                    name=name, 
                    phone=phone
                )
                user.save()
                messages.success(request, "Your account has been created successfully!")
                return redirect('login')
            except Exception as e:
                messages.error(request, f"There was an error creating your account: {str(e)}")
        else:
            messages.error(request, "Passwords do not match.")
    return render(request, 'authentication/register.html')

def login_page(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Authenticate user with email and password
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, "You have successfully logged in.")
            return redirect('home')
        else:
            messages.error(request, "Invalid email or password.")
    return render(request, 'authentication/login.html')

@login_required
def logout_page(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect('login')
