from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, Permission

from Agency.models import Employee
from Users.models import User


class UserRegistrationForm(UserCreationForm):
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name','last_name', 'email','password1', 'password2', 'employee', 'is_admin')




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