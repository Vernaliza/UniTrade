# from django.contrib.auth.decorators import login_required
# from django.shortcuts import render, redirect
# from django.contrib import messages

# def administrator():
#     return 0

# def admin_user_ban_management():
#     return 0

# def admin_user_delete_management():
#     return 0

# def admin_user_authority_given_management():
#     return 0

# def admin_item_management():
#     return 0

# def admin_report_management():
#     return 0

# def admin_account_management():
#     return 0

# def admin_notification_management():
#     return 0
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

# Security check: Only allow users marked as "is_staff"
def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin, login_url='/user/login/')
def admin_dashboard(request):
    users = User.objects.select_related('profile').all().order_by('-date_joined')
    return render(request, 'administrator/dashboard.html', {'users': users})

@user_passes_test(is_admin, login_url='/user/login/')
def delete_user(request, user_id):
    if request.method == 'POST':
        user_to_delete = get_object_or_404(User, id=user_id)
        
        # 1. Prevent admins from deleting themselves!
        if user_to_delete == request.user:
            messages.error(request, "Security Error: You cannot delete your own active admin account.")
        # 2. Prevent accidental deletion of other superusers
        elif user_to_delete.is_superuser:
            messages.error(request, "Security Error: You cannot delete a Superuser from this dashboard.")
        # 3. Safe to delete normal users
        else:
            deleted_username = user_to_delete.username
            user_to_delete.delete()  # This deletes the user and their linked Profile
            messages.success(request, f"User '{deleted_username}' has been successfully deleted.")
            
    return redirect('administrator:dashboard')