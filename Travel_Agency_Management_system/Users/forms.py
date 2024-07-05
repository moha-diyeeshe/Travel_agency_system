from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm,UserChangeForm
from django.contrib.auth.models import Group, Permission

from Agency import models
from Agency.models import Employee
from Users.models import User

from django.db.models import Q


class UserRegistrationForm(UserCreationForm):
    employee = forms.ModelChoiceField(queryset=Employee.objects.filter(user__isnull=True), required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'employee', 'is_admin')

    def save(self, commit=True):
        user = super().save(commit=False)
        employee = self.cleaned_data.get('employee')

        is_admin = self.cleaned_data.get('is_admin', False)

        if commit:
            user.save()
            # Ensure that the Admin group exists before trying to add or remove the user
            admin_group, created = Group.objects.get_or_create(name='Admin')
            if is_admin:
                admin_group.user_set.add(user)
            else:
                admin_group.user_set.remove(user)

            self.save_m2m()  # Save many-to-many fields if there are any

        return user



class UserUpdateForm(UserChangeForm):
    password = None  # Disable password field since we're not editing it here
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(user__isnull=True),
        required=False
    )
    is_admin = forms.BooleanField(label="Admin", required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'employee', 'is_admin')

    def __init__(self, *args, **kwargs):
        user_instance = kwargs.get('instance', None)
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        # Set employee queryset based on whether a user instance is provided
        if user_instance and hasattr(user_instance, 'employee'):
            self.fields['employee'].queryset = Employee.objects.filter(
                Q(user__isnull=True) | Q(user=user_instance)
            )
        else:
            self.fields['employee'].queryset = Employee.objects.filter(user__isnull=True)

    def save(self, commit=True):
        user = super().save(commit=False)
        employee = self.cleaned_data.get('employee')

        is_admin = self.cleaned_data.get('is_admin', False)

        if commit:
            user.save()
            # Ensure that the Admin group exists before trying to add or remove the user
            admin_group, created = Group.objects.get_or_create(name='Admin')
            if is_admin:
                admin_group.user_set.add(user)
            else:
                admin_group.user_set.remove(user)

            self.save_m2m()  # Save many-to-many fields if there are any

        return user


class GroupForm(forms.ModelForm):

    class Meta:
        model = Group
        fields = ['name', 'permissions']



class UserGroupsForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = User
        fields = ['groups']