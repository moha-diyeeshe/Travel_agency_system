from django.utils import timezone
import uuid
from django.db import models
from django.db import models, transaction as db_transaction
from django.contrib.auth.models import AbstractUser

from Users.models import User





class TransactionReference(models.Model):
    # No fields needed besides the automatically created 'id' which will auto-increment
    
    def save(self, *args, **kwargs):
        # Custom save method to start ids from 5000
        with db_transaction.atomic():
            if not self.pk:
                last_ref = TransactionReference.objects.last()
                if last_ref is None:
                    # This is the first entry, set initial id to 4999 so next is 5000
                    self.id = 4999
            super().save(*args, **kwargs)








class Customer(models.Model):
    name = models.CharField(max_length=80)
    phone = models.CharField(max_length=15)
    reference_name = models.CharField(max_length=80)
    reference_phone = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=80) 
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


    def __str__(self):
        return self.name


class Country(models.Model):
    name = models.CharField(max_length=100)
    nationality = models.CharField(max_length=100)


    def __str__(self):
        return self.name
    
    
class City(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    transaction_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    TRANSACTION_TYPE_CHOICES = [
        ('ticket', 'Ticket'),
        ('visa', 'Visa')
    ]
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    PAYMENT_METHOD_CHOICES = [
        ('bank', 'Bank'),
        ('evc_plus', 'EVC Plus'),
        ('edahab', 'Edahab')
    ]
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    reference_number = models.CharField(max_length=100, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('partial', 'Partial'), ('paid', 'Paid')], default='pending')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Transaction {self.reference_number} - {self.customer.name}"

    def save(self, *args, **kwargs):
        if not self.pk:  # Check if this is a new record
            with db_transaction.atomic():  # Use atomic to avoid race conditions
                ref = TransactionReference.objects.create()
                self.reference_number = f"INVOICE{ref.id:04d}"  # Pads the ID to ensure it is 12 digits long
        super(Transaction, self).save(*args, **kwargs)

    def update_status(self):
        if self.paid_amount >= self.total_amount:
            self.status = 'paid'
        elif self.paid_amount > 0:
            self.status = 'partial'
        else:
            self.status = 'pending'
        self.save()

class Payment(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=Transaction.PAYMENT_METHOD_CHOICES)
    payment_date = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Payment {self.amount} for {self.transaction.reference_number}"

class TicketBooking(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    passenger_name = models.CharField(max_length=100)
    pnr = models.CharField(max_length=50 ) 
    age_category = models.CharField(max_length=3, choices=(('ADT', 'Adult'), ('CHD', 'Child')))
    travel_date = models.DateField()
    fare = models.DecimalField(max_digits=9, decimal_places=2)
    commission = models.DecimalField(max_digits=9, decimal_places=2 )
    tax = models.DecimalField(max_digits=9, decimal_places=2)
    sell_fare = models.DecimalField(max_digits=9, decimal_places=2)
    from_city = models.ForeignKey(City, related_name='booking_departures', on_delete=models.CASCADE)
    destination = models.ForeignKey(City, related_name='booking_destinations', on_delete=models.CASCADE)
    back_to = models.ForeignKey(City, related_name='booking_returns', on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=15)
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE)
    visa_status =[('confirmed', 'Confirmed'), ('canceled', 'Canceled'), ('pending', 'Pending')]
    status = models.CharField(max_length=10, choices= visa_status , default='pending')
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    booking_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.passenger_name} - {self.supplier.name}"

class VisaBooking(models.Model):
    AGE_CHOICES = [
        ('ADT', 'Adult'),
        ('CHD', 'Child'),
        ('inf', 'INF'),
    ]
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, related_name='visa_country', on_delete=models.CASCADE)
    nationality = models.ForeignKey(Country, related_name='visa_nationality', on_delete=models.CASCADE)
    departure_date = models.DateField()
    visa_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    phone = models.CharField(max_length=15)
    photo = models.ImageField(upload_to='applicant_photos/', null=True, blank=True)
    passport_copy = models.FileField(upload_to='passport_copies/', null=True, blank=True)
    age_group = models.CharField(max_length=3, choices=AGE_CHOICES)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    ticket_status = [('confirmed', 'Confirmed'), ('canceled', 'Canceled'), ('pending', 'Pending')]
    status = models.CharField(max_length=10, choices= ticket_status, default='pending')
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Expense(models.Model):
    EXPENSE_CATEGORY_CHOICES = [
        ('rent', 'Rent'),
        ('utilities', 'Utilities'),
        ('supplies', 'Supplies'),
        ('salary', 'Salary'),
        ('other', 'Other'),
    ]

    category = models.CharField(max_length=50, choices=EXPENSE_CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    payment_method = models.CharField(max_length=50, choices=Transaction.PAYMENT_METHOD_CHOICES)
    date_created = models.DateTimeField(default=timezone.now)
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.get_category_display()} - {self.amount}"

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=50)
    phone = models.CharField(max_length=50)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    title = models.CharField(max_length=50)
    profile_photo = models.ImageField(upload_to='profile_pics/')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    # reference_name = models.CharField(max_length=50)
    # reference_number = models.CharField(max_length=50)








class Asset(models.Model):
    asset_name = models.CharField(max_length=255)
    purchase_date = models.DateField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.asset_name} purchased on {self.purchase_date}"
