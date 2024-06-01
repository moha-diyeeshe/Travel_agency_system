from django.shortcuts import render
from django.shortcuts import render,get_object_or_404,redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.contrib import messages
from Users.forms import GroupForm, UserGroupsForm, UserRegistrationForm
from Users.models import ActivityLog, User
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group, Permission

# Create your views here.
@login_required
@permission_required('Agency.add_user', raise_exception=True)
def user_register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
             new_user = form.save(commit=False)
             new_user.user = request.user
             new_user.save()
             return redirect('index')  # Redirect to your desired page after successful registration
        else:
            # It's helpful to print form errors to debug in development environments
            print(form.errors)    
    else:
        form = UserRegistrationForm()
    
    return render(request, 'Dashboard/users/add_user.html', {'form': form})




@permission_required('Agency.view_user', raise_exception=True)
def user_list(request):
    users = User.objects.all()
    return render(request, 'Dashboard/users/manage_users.html', {'users': users})


@login_required
@permission_required('Agency.view_permission', raise_exception=True)
def manage_users(request):
    users = User.objects.all()
    return render(request, 'Dashboard/users/user_permissions.html', {'users': users})


@login_required
def user_change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password1')
        confirm_password = request.POST.get('new_password2')

        user = request.user

        if not check_password(current_password, user.password):
            messages.error(request, "Current password is incorrect.")
        elif new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
        else:
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)  # Keep the user logged in after password change
            messages.success(request, 'Your password has been successfully updated.')
            return redirect('index')  # Ensure this is the correct redirect path

    return render(request, 'Dashboard/users/change_password.html')





@login_required
@permission_required('Agency.add_customuser', raise_exception=True)
def admin_change_user_password(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        new_password = request.POST.get('new_password1')
        confirm_password = request.POST.get('new_password2')

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
        else:
            target_user.set_password(new_password)
            target_user.save()
            messages.success(request, f"Password for {target_user.username} has been updated.")
            return redirect('user_list')  # Redirect to a page listing all users

    return render(request, 'Dashboard/users/admin_change_password.html', {'user': target_user})



@login_required
@permission_required('Agency.change_permission', raise_exception=True)
def edit_permissions(request, user_id):
    user = get_object_or_404(User, id=user_id)
    all_permissions = Permission.objects.all().select_related('content_type')
    user_permissions = user.user_permissions.all()

    if request.method == 'POST':
        selected_permissions = request.POST.getlist('permissions')
        user.user_permissions.set(selected_permissions)
        user.save()
        messages.success(request, 'Permissions updated successfully.')
        return redirect('manage_users')

    context = {
        'user': user,
        'permissions': all_permissions,
        'user_permissions': user_permissions
    }
    return render(request, 'Dashboard/users/edit_permissions.html', context)




def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_superuser:
                    print("This user is a superuser and has all permissions.")

                return redirect('index')  # Redirect to the home page or another page
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'Dashboard/login.html', {'form': form})



@login_required
def user_logout(request):
    logout(request)
    return redirect('login')




@login_required
@permission_required('Agency.view_activitylog', raise_exception=True)
def activity_log(request):
    logs = ActivityLog.objects.all().order_by('-timestamp')  # Ordering by timestamp desc
    return render(request, 'Dashboard/activity_log.html', {'logs': logs})







def create_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')  # Redirect to a view that shows all groups
    else:
        form = GroupForm()

    return render(request, 'Dashboard/users/add_group.html', {'form': form})




def manage_groups(request):
    groups = Group.objects.all()
    return render(request,'Dashboard/users/manage_groups.html',{'groups':groups})




def edit_group_permissions(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.method == 'POST':
        group.permissions.clear()
        permissions = request.POST.getlist('permissions')
        for perm_id in permissions:
            perm = Permission.objects.get(id=perm_id)
            group.permissions.add(perm)
        messages.success(request, 'Permissions updated successfully.')
        return redirect('manage_groups')

    permissions = Permission.objects.all()
    group_permissions = group.permissions.all()
    return render(request, 'Dashboard/users/group_permissions.html', {
        'group': group,
        'permissions': permissions,
        'group_permissions': group_permissions
    })




def assign_groups(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = UserGroupsForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Groups updated successfully.")
            return redirect('user_list')  # Redirect to the user list or another appropriate page
    else:
        form = UserGroupsForm(instance=user)

    return render(request, 'Dashboard/users/assign_user_group.html', {
        'form': form,
        'user': user
    })