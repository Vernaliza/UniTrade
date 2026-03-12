from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserLoginForm, UserRegisterForm
# def user_login(request):
#     if request.method == 'POST':
#         form = UserLoginForm(request.POST)
#         if form.is_valid():
#             username = form.cleaned_data['username']
#             password = form.cleaned_data['password']
#             user = authenticate(username=username, password=password)
#             if user is not None:
#                 login(request, user)
#                 messages.success(request, 'Login successful!')
#                 next_url = request.GET.get('next', '/')
#                 return redirect(next_url)
#             else:
#                 messages.error(request, 'Invalid username or password!')
#     else:
#         form = UserLoginForm()

#     return render(request, 'user/login.html', {'form': form})

# user/views.py
def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Login successful!')
                
                # NEW REDIRECT LOGIC
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                else:
                    # This sends them to your dashboard_redirect logic!
                    return redirect('user:dashboard') 
            else:
                messages.error(request, 'Invalid username or password!')
    else:
        form = UserLoginForm()

    return render(request, 'user/login.html', {'form': form})



def user_register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('index')
        else:
            messages.error(request, 'Registration failed!')
    else:
        form = UserRegisterForm()
    

    return render(request, 'user/register.html', {'form': form})


@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'Successfully logged out!')
    return redirect('index')

@login_required
def dashboard_redirect(request):
    """
    Redirects users based on their role after login.
    Admins go to 'Admin Panel', Merchants go to 'My Shop', Students go to 'Browse'.
    """
    
    # 1. NEW LOGIC: Check if the user is an Admin first!
    if request.user.is_staff:
        return redirect('administrator:dashboard')

    # 2. Existing logic for normal users
    try:
        role = request.user.profile.role
    except AttributeError:
        # Default fallback if no profile exists
        return redirect('item:item_list')

    if role == 'merchant':
        # Merchants manage their listings
        return redirect('item:my_item')
    else:
        # Students browse the marketplace
        return redirect('item:item_list')
    
@login_required(login_url='/user/login/')
def profile_view(request):
    # for display user info
    return render(request, 'user/profile.html', {'user': request.user})

@login_required(login_url='/user/login/')
def profile_edit(request):
    if request.method == 'POST':
        # recive new data from form
        new_email = request.POST.get('email')
        new_address = request.POST.get('address')

        # update user email in django's built-in User model
        user = request.user
        user.email = new_email
        user.save()

        # update user address in Profile model
        if hasattr(user, 'profile'):
            user.profile.address = new_address
            user.profile.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('user:profile')

    # if GET request, show the edit form with current user info
    return render(request, 'user/profile_edit.html', {'user': request.user})