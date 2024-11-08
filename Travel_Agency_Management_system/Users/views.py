from django.shortcuts import render
from django.shortcuts import render,get_object_or_404,redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.contrib import messages
from django.urls import reverse
from Agency.views import log_action
from Users.forms import GroupForm, UserGroupsForm, UserRegistrationForm, UserUpdateForm
from Users.models import ActivityLog, AuditTrials, ErrorLogs, User
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group, Permission
from django.db.models import Q

from django.contrib.sessions.models import Session


from django.core.paginator import Paginator

from Users.utils import log_error

from django.contrib.contenttypes.models import ContentType


# Create your views here.
@login_required
@permission_required('Users.add_user', raise_exception=True)
def user_register(request):
    try:
        if request.method == 'POST':
            form = UserRegistrationForm(request.POST)
            if form.is_valid():
                new_user = form.save()
                log_action(request.user, 'created',  f"{new_user}  registered .")

                messages.success(request, "User successfully registered.")
                return redirect('user_list')  # Redirect to your desired page after successful registration
            else:
                messages.error(request, "Error during registration. Please check the form for errors.")
        else:
            form = UserRegistrationForm()

        return render(request, 'Dashboard/users/add_user.html', {'form': form})
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An unexpected error occurred during registration.")
        return render(request, 'Dashboard/users/add_user.html', {'form': form})



@login_required
@permission_required('Users.change_user', raise_exception=True)
def edit_user(request, user_id):
    try:
        user = get_object_or_404(User, pk=user_id)
        if request.method == 'POST':
            form = UserUpdateForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                log_action(request.user, 'updated',  f"User {user.username} updated.")
                messages.success(request, 'User updated successfully!')
                return redirect('user_list')  # Adjust this to your correct redirect

            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = UserUpdateForm(instance=user)

        return render(request, 'Dashboard/users/edit_user.html', {'form': form,'user': user })
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An unexpected error occurred while updating user.")
        return render(request, 'Dashboard/users/edit_user.html', {'form': [], 'user': user})


@login_required
@permission_required('Users.add_user', raise_exception=True)
def user_list(request):
    try:
        users = User.objects.all().order_by('-modified_at')  # Sorting users by join date
        paginator = Paginator(users, 10)  # Show 10 users per page

        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'Dashboard/users/manage_users.html', {'page_obj': page_obj})
    except Exception as e:
        log_error(request, e)
        messages.error(request, "Failed to retrieve users.")
        return render(request, 'Dashboard/users/manage_users.html', {'page_obj': page_obj})





@login_required
def user_change_password(request):
    try:
        if request.method == 'POST':
            current_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password1')
            confirm_password = request.POST.get('new_password2')

            user = request.user

            if not check_password(current_password, user.password):
                messages.error(request, "Current password is incorrect.")
                log_action(user, 'password change attempt failed', 'Incorrect current password')
            elif new_password != confirm_password:
                messages.error(request, "New passwords do not match.")
                log_action(user, 'password change attempt failed', 'Mismatched new passwords')
            else:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  # Keep the user logged in after password change
                messages.success(request, 'Your password has been successfully updated.')
                log_action(user, 'password changed', 'Password updated successfully')
                return redirect('index')  # Ensure this is the correct redirect path

        return render(request, 'Dashboard/users/change_password.html')
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while changing the password.")
        log_action(request.user, 'password change error', 'Error during password change')
        return render(request, 'Dashboard/users/change_password.html')


def log_action(user, action, description=""):
    """Log user actions to the ActivityLog model."""
    ActivityLog.objects.create(
        user=user,
        action=action,
        description=description,
        content_type=ContentType.objects.get_for_model(user.__class__),
        object_id=user.pk,
    )

@login_required
@permission_required('Users.add_user', raise_exception=True)
def admin_change_user_password(request, user_id):
    try:
        target_user = get_object_or_404(User, pk=user_id)
        if request.method == 'POST':
            new_password = request.POST.get('new_password1')
            confirm_password = request.POST.get('new_password2')

            if new_password != confirm_password:
                messages.error(request, "New passwords do not match.")
                log_action(target_user, 'password change failed', request.user, f"Attempted password change for {target_user.username} failed due to mismatch.")
            else:
                target_user.set_password(new_password)
                target_user.save()
                Session.objects.filter(session_key__in=target_user.get_session_auth_hash()).delete()
                messages.success(request, f"Password for {target_user.username} has been updated.")
                log_action( target_user,  'password changed',  f"Password changed by {request.user.username}: Password for {target_user.username} successfully changed.")
                update_session_auth_hash(request, target_user)
                return redirect('user_list')  # Redirect to a page listing all users

        return render(request, 'Dashboard/users/admin_change_password.html', {'user': target_user})
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while updating the user's password.")
        return render(request, 'Dashboard/users/admin_change_password.html', {'user': target_user})



@login_required
@permission_required('Users.change_permission', raise_exception=True)
def edit_permissions(request, user_id):
    try:
        user = get_object_or_404(User, id=user_id)
        all_permissions = Permission.objects.all().select_related('content_type')
        user_permissions = user.user_permissions.all()

        if request.method == 'POST':
            selected_permissions = request.POST.getlist('permissions')
            user.user_permissions.set(selected_permissions)
            user.save()
            log_action(user, 'permissions updated', request.user, f"Permissions updated for {user.username}.")
            messages.success(request, 'Permissions updated successfully.')
            return redirect('manage_users')

        context = {
            'user': user,
            'permissions': all_permissions,
            'user_permissions': user_permissions
        }
        return render(request, 'Dashboard/users/edit_permissions.html', context)
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while updating permissions.")
        return render(request, 'Dashboard/users/edit_permissions.html', {
            'user': user,
            'permissions': all_permissions,
            'user_permissions': user_permissions,
            'error': 'An unexpected error occurred'
        })
    




def user_login(request):
    try:
        if request.method == 'POST':
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    # Assuming `user` is the User instance of the successfully logged-in user.
                    log_action(user, 'login', f"Successful login for {user.username}")


                    return redirect('index')  # Redirect to the home page or another page
                else:
                    messages.error(request, 'Invalid username or password.')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            form = AuthenticationForm()
        return render(request, 'Dashboard/login.html', {'form': form})
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred during login.")
        return render(request, 'Dashboard/login.html', {'form': form})



@login_required
def user_logout(request):
    try:
        user = request.user
        if user.is_authenticated:
            log_action(user, 'logout', f"User {user.username} logged out successfully.")
        logout(request)
        return redirect('login')
    except Exception as e:
        log_error(request, e, 'Failed to logout user.')
        return redirect('login')




@login_required
@permission_required('Users.view_activitylog', raise_exception=True)
def activity_log(request):
    try:
        logs = ActivityLog.objects.all().order_by('-timestamp')  # Ordering by timestamp desc
        return render(request, 'Dashboard/activity_log.html', {'logs': logs})
    except Exception as e:
        log_error(request, e)
        messages.error(request, "Failed to retrieve activity logs.")
        return render(request, 'Dashboard/error.html', {'logs': logs})






@login_required
@permission_required('auth.manage_role_groups', raise_exception=True)
def create_group(request):
    try:
        if request.method == 'POST':
            form = GroupForm(request.POST)
            if form.is_valid():
                new_group=form.save()
                log_action(request.user, 'create group', f"Group {new_group.name} created successfully.")
                return redirect('index')  # Redirect to a view that shows all groups
        else:
            form = GroupForm()

        return render(request, 'Dashboard/users/add_group.html', {'form': form})
    except Exception as e:
        log_error(request, e)
        messages.error(request, "Failed to create group.")
        return render(request, 'Dashboard/users/add_group.html', {'form': form})



@login_required
@permission_required('auth.manage_role_groups', raise_exception=True)
def manage_groups(request):
    try:
        query = request.GET.get('query', '')  # Capture the search query
        if query:
            groups = Group.objects.filter(name__icontains=query)
        else:
            groups = Group.objects.all().order_by('-name')
        
        paginator = Paginator(groups, 10)  # Show 10 groups per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'Dashboard/users/manage_groups.html', {'page_obj': page_obj, 'query': query})
    except Exception as e:
        log_error(request, e)
        messages.error(request, "Failed to manage groups.")
        return render(request, 'Dashboard/users/manage_groups.html',{'page_obj': page_obj, 'query': query})



@login_required
@permission_required('auth.add_permission', raise_exception=True)
def edit_group_permissions(request, group_id):
    try:
        group = get_object_or_404(Group, id=group_id)
        if request.method == 'POST':
            group.permissions.clear()
            permissions = request.POST.getlist('permissions')
            for perm_id in permissions:
                perm = Permission.objects.get(id=perm_id)
                group.permissions.add(perm)
            log_action(request.user, 'update group permissions', f"Permissions updated for group {group.name}.")
            messages.success(request, 'Permissions updated successfully.')
            return redirect('manage_groups')

        permissions = Permission.objects.all()
        group_permissions = group.permissions.all()
        return render(request, 'Dashboard/users/group_permissions.html', {
            'group': group,
            'permissions': permissions,
            'group_permissions': group_permissions
        })
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while updating group permissions.")
        return render(request, 'Dashboard/users/group_permissions.html', {
            'group': group
        })



@login_required
@permission_required('auth.assign_user_to_group', raise_exception=True)
def assign_groups(request, user_id):
    try:
        user = get_object_or_404(User, pk=user_id)
        if request.method == 'POST':
            form = UserGroupsForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                log_action(request.user, 'assign groups', f"Updated group assignments for {user.username}.")
                messages.success(request, "Groups updated successfully.")
                return redirect('user_list')  # Redirect to the user list or another appropriate page
        else:
            form = UserGroupsForm(instance=user)
        return render(request, 'Dashboard/users/assign_user_group.html', {
            'form': form,
            'user': user
        })
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while assigning groups.")
        return render(request, 'Dashboard/users/assign_user_group.html', {
            'form': form,
            'user': user
        })




@login_required
@permission_required('Users.view_errorlogs', raise_exception=True)
def error_logs(request):
    try:
        query = request.GET.get('query', '')

        # Filtering based on a search query
        if query:
            logs = ErrorLogs.objects.filter(
                Q(Username__icontains=query) |
                Q(Name__icontains=query) |
                Q(Expected_error__icontains=query) |
                Q(field_error__icontains=query)
            ).order_by('-date_recorded')
        else:
            logs = ErrorLogs.objects.all().order_by('-date_recorded')

        # Setup pagination
        paginator = Paginator(logs, 10)  # Display 10 logs per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'Dashboard/logs/error_logs.html', {'page_obj': page_obj, 'query': query})
    except Exception as e:
        log_error(request, e)
        messages.error(request, "Failed to retrieve error logs.")
        return render(request, 'Dashboard/logs/error_logs.html',{'page_obj': page_obj, 'query': query})
    



@login_required
@permission_required('Users.view_audittrials', raise_exception=True)
def audit_trails(request):
    try:
        logs_list = AuditTrials.objects.all().order_by('-date_of_action')
        paginator = Paginator(logs_list, 20)  # Show 10 logs per page

        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'Dashboard/logs/audit_trails.html', {'page_obj': page_obj})
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while trying to display audit trails.")
        # Redirect or render a specific template if the error affects the page rendering
        return render(request, 'Dashboard/logs/audit_trails.html', {'page_obj': page_obj})
    
















def custom_404(request, exception):
    return render(request, 'Dashboard/errors/404.html', status=404)

def custom_500(request):
    return render(request, 'Dashboard/errors/500.html', status=500)




def custom_403(request, exception):
    return render(request, 'Dashboard/errors/403.html', status=403)






@login_required
@permission_required('auth.change_user')
def toggle_user_active(request, user_id):
    try:
        user = get_object_or_404(User, id=user_id)
        user.is_active = not user.is_active  # Toggle the is_active field
        user.save()
        messages.success(request, f"User {'activated' if user.is_active else 'deactivated'} successfully.")
        return redirect(reverse('user_management'))
    except Exception as e:
        log_error(request,e)
        messages.error(request, "An error occured while trying to activate user")
        return redirect('index')


