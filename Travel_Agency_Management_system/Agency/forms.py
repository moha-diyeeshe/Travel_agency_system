from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import  Group
from Agency.models import Asset, City,  Customer, Employee, Expense, Payment, Supplier, TicketBooking, Transaction, VisaBooking


# customer registeration
class CustomerRegistrationForm(ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'reference_name', 'reference_phone']

#Supplier registeration
class SupplierRegistrationForm(ModelForm):
    class Meta:
        model = Supplier
        fields = ['name' ]


#customer update form
class CustomerUpdateForm(ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'reference_name', 'reference_phone']



#supplier Update form
class SupplierUpdateForm(ModelForm):
    class Meta:
        model = Supplier
        fields = ['name']

# class SupplierUpdateForm(ModelForm):
#     class Meta:
#         model = City
#         fields = ['name']



class BookingForm(ModelForm):
    class Meta:
        model = TicketBooking
        fields = ['customer', 'supplier', 'passenger_name','fare','commission','tax','sell_fare','age_category', 'pnr', 'travel_date','from_city', 'destination', 'back_to', 'phone','status',]


class cityForm(ModelForm):
    class Meta:
        model = City
        fields = ['name']




class VisaBookingForm(ModelForm):
    class Meta:
        model = VisaBooking
        fields = ['age_group','name','nationality','country','departure_date', 'visa_fee', 'commission','phone', 'photo','passport_copy','customer','status']



class PaymentForm(ModelForm):
    class Meta:
        model = Transaction
        fields = ['payment_method', 'paid_amount']


class BookingSelectionForm(forms.Form):
    bookings = forms.ModelMultipleChoiceField(
        queryset=TicketBooking.objects.filter(status='pending'),
        widget=forms.CheckboxSelectMultiple,
        label="Select Bookings"
    )

    def __init__(self, *args, **kwargs):
        transaction_type = kwargs.pop('transaction_type', None)
        super().__init__(*args, **kwargs)
        if transaction_type == 'visa':
            self.fields['bookings'].queryset = VisaBooking.objects.filter(status='pending')


class CompletePaymentForm(ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_method', 'amount']



class DateSelectionForm(forms.Form):
    selected_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))







class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'amount', 'description', 'payment_method']


# employee for fo the HR
class EmployeeForm(ModelForm):
    class Meta:
        model = Employee
        fields = ['name', 'address','phone','salary','title','profile_photo',]



class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['asset_name', 'purchase_date', 'purchase_price', 'description',]







