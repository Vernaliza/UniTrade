from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserLoginForm, UserRegisterForm
import random
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from .forms import PasswordChangeCustomForm
from .models import Profile
from django.views.decorators.http import require_POST
from .forms import ForgotPasswordEmailForm, EmailCodeForm, ResetPasswordForm
import time

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

#user/views.py
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



# def user_register(request):
#     if request.method == 'POST':
#         form = UserRegisterForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             login(request, user)
#             messages.success(request, 'Registration successful!')
#             return redirect('index')
#         else:
#             messages.error(request, 'Registration failed!')
#     else:
#         form = UserRegisterForm()
#
#
#     return render(request, 'user/register.html', {'form': form})

def user_register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            code = str(random.randint(100000, 999999))

            request.session['register_data'] = request.POST.dict()
            request.session['email_verification_code'] = code

            # if settings.DEBUG:#There will only be a pop-up window when debug=True! When debug=False, the captcha is in your terminal
            #     messages.success(request, f'Test verification code: {code}')
            # else:
            #     send_mail(
            #         subject='Your UniTrade verification code',
            #         message=f'Your verification code is: {code}',
            #         from_email=settings.DEFAULT_FROM_EMAIL,
            #         recipient_list=[form.cleaned_data['email']],
            #         fail_silently=False,
            #     )
            #     messages.success(request, 'Verification code has been sent to your email.')
            send_mail(
                subject='Your UniTrade verification code',
                message=f'Your verification code is: {code}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[form.cleaned_data['email']],
                fail_silently=False,
            )
            messages.success(request, 'Verification code has been sent to your email.')
            return redirect('user:verify_email')
    else:
        form = UserRegisterForm()

    return render(request, 'user/register.html', {'form': form})

def verify_email(request):
    if request.method == 'POST':
        user_code = request.POST.get('code')
        real_code = request.session.get('email_verification_code')
        register_data = request.session.get('register_data')

        if not register_data:
            messages.error(request, 'Registration session expired. Please register again.')
            return redirect('user:user_register')

        if user_code == real_code:
            form = UserRegisterForm(register_data)
            if form.is_valid():
                form.save()

                request.session.pop('register_data', None)
                request.session.pop('email_verification_code', None)

                messages.success(request, 'Registration successful. Please log in.')
                return redirect('user:user_login')
            else:
                print(form.errors)
                messages.error(request, f'Registration data is invalid: {form.errors}')
                return redirect('user:user_register')
        else:
            messages.error(request, 'Invalid verification code.')

    return render(request, 'user/verify_email.html')


# def user_login(request):
#     return redirect('account_login')
#
#
# def user_register(request):
#     return redirect('account_signup')

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
        
        # --- NEW: Get the uploaded file ---
        new_avatar = request.FILES.get('avatar')

        # update user email 
        user = request.user
        user.email = new_email
        user.save()

        # update user address and avatar in Profile model
        if hasattr(user, 'profile'):
            user.profile.address = new_address
            # --- NEW: Save the avatar if one was uploaded ---
            if new_avatar:
                user.profile.avatar = new_avatar
            user.profile.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('user:profile')

    # if GET request, show the edit form with current user info
    return render(request, 'user/profile_edit.html', {'user': request.user})


@login_required
def change_password(request):

    if request.method == 'POST':
        form = PasswordChangeCustomForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()

            update_session_auth_hash(request, user)

            return redirect('user:profile')#I don't know where should we redirect. You can change it
    else:
        form = PasswordChangeCustomForm(request.user)

    return render(request, 'user/change_password.html', {
        'form': form
    })


@login_required
@require_POST
def toggle_role(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if profile.role == Profile.Role.MERCHANT:
        profile.role = Profile.Role.STUDENT
        messages.success(request, 'Switched to Student/Buyer mode.')
    else:
        profile.role = Profile.Role.MERCHANT
        messages.success(request, 'Switched to Merchant/Seller mode.')

    profile.save()

    next_url = request.POST.get('next')
    return redirect(next_url or 'user:dashboard')

@login_required
def test_toggle_role(request):#just for test
    return render(request, 'user/test_toggle_role.html')


def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            code = str(random.randint(100000, 999999))

            request.session['reset_email'] = email
            request.session['password_reset_code'] = code
            request.session['password_reset_code_time'] = int(time.time())
            request.session['password_reset_verified'] = False

            send_mail(
                subject='Your password reset verification code',
                message=f'Your verification code is: {code}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            messages.success(request, 'Verification code has been sent to your email.')
            return redirect('user:verify_reset_code')
    else:
        form = ForgotPasswordEmailForm()

    return render(request, 'user/forgot_password.html', {'form': form})


def verify_reset_code(request):
    if request.method == 'POST':
        form = EmailCodeForm(request.POST)
        if form.is_valid():
            user_code = form.cleaned_data['code']
            real_code = request.session.get('password_reset_code')
            code_time = request.session.get('password_reset_code_time')

            if not real_code or not code_time:
                messages.error(request, 'Session expired. Please request a new code.')
                return redirect('user:forgot_password')

            # if int(time.time()) - code_time > 300:
            #     messages.error(request, 'Verification code expired. Please request a new code.')
            #     return redirect('user:forgot_password')

            if user_code == real_code:
                request.session['password_reset_verified'] = True
                messages.success(request, 'Verification successful. Please reset your password.')
                return redirect('user:reset_password')
            else:
                messages.error(request, 'Invalid verification code.')
    else:
        form = EmailCodeForm()

    return render(request, 'user/verify_reset_code.html', {'form': form})


def reset_password(request):

    if not request.session.get('password_reset_verified'):
        return redirect('user:forgot_password')

    email = request.session.get('reset_email')
    user = User.objects.get(email=email)

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)

        if form.is_valid():
            user.set_password(form.cleaned_data['new_password1'])
            user.save()

            request.session.pop('reset_email', None)
            request.session.pop('password_reset_code', None)
            request.session.pop('password_reset_code_time', None)
            request.session.pop('password_reset_verified', None)

            messages.success(request, "Password reset successful. Please log in.")

            return redirect('user:user_login')

    else:
        form = ResetPasswordForm()

    return render(request, 'user/reset_password.html', {'form': form})

