from datetime import date, datetime, timedelta, timezone
from django.shortcuts import render,get_object_or_404,redirect
from django.db.models import Q, Count, Sum


from django.core.paginator import Paginator
from Agency import models
from Agency.forms import AssetForm, BookingForm, BookingSelectionForm, CompletePaymentForm, CustomerRegistrationForm, CustomerUpdateForm, DateSelectionForm, EmployeeForm, ExpenseForm, PaymentForm, SupplierRegistrationForm, SupplierUpdateForm,  VisaBookingForm, cityForm
from Agency.models import Asset, City,  Customer, Employee, Expense, Payment, Supplier, TicketBooking, Transaction, VisaBooking 
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F, Sum, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone

from django.db.models import Value, CharField
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
from decimal import Decimal
from django.utils.dateparse import parse_date
from django.db import transaction as db_transaction
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.decorators import login_required, permission_required

from django.contrib.auth import login, authenticate, logout

from Users.models import ActivityLog, User
from django.db.models.functions import TruncMonth



@login_required
@permission_required('Agency.view_customer', raise_exception=True)
def customers_list(request):
    # Start with a query that will fetch all customers by default, ordered by creation date
    customers = Customer.objects.all().order_by('-created_at')
    
    # Get the search query from the request, if provided
    query = request.GET.get('query', '')

    # Filter the customer list if a query is present
    if query:
        customers = customers.filter(
            Q(phone__icontains=query) | 
            Q(name__icontains=query)
        )
    
    # Setup pagination
    paginator = Paginator(customers, 10)  # Show 10 customers per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Render the customers list (filtered or unfiltered) to the template
    # Include page_obj to provide paginated customers and the query for persistence in the search bar
    return render(request, 'Dashboard/customers/customers.html', {'page_obj': page_obj, 'query': query})









# the customers registeration function 
@login_required
@permission_required('Agency.add_customer', raise_exception=True)
def customer_registration(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            new_customer = form.save(commit=False)
            new_customer.user = request.user
            new_customer.save()
            # Redirect to a success page or wherever you want
            messages.success(request, 'Customer registered successfully!')
            return redirect('customers')
            
    else:
        form = CustomerRegistrationForm()
    return render(request, 'Dashboard/customers/customer_register.html', {'form': form})









#customers update 
@login_required
@permission_required('Agency.change_customer', raise_exception=True)
def customer_update(request, id):
    customer = get_object_or_404(Customer, id=id)
    if request.method == 'POST':
        form = CustomerUpdateForm(request.POST, instance=customer)
        if form.is_valid():
            updated_customer = form.save(commit=False)
            updated_customer.user = request.user
            updated_customer.save()
            messages.success(request, 'Customer information updated successfully!')
            return redirect('customers')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = CustomerUpdateForm(instance=customer)

    context ={
        'form': form,
        'customer': customer
    }
    
    return render(request, 'Dashboard/customers/customer_update_form.html', context)







# supplier registeration 
@login_required
@permission_required('Agency.add_supplier', raise_exception=True)
def supplier_registration(request):
    if request.method == 'POST':
        form = SupplierRegistrationForm(request.POST)
        if form.is_valid():
            new_Supplier = form.save(commit=False)
            new_Supplier.user = request.user
            new_Supplier.save() 
            return redirect('suppliers_list')  # Redirect to a success page or another URL
    else:
        form = SupplierRegistrationForm()

    context = {
        'form': form
    }
    return render(request,'Dashboard/suppliers/supplier_registration.html')






@login_required
@permission_required('Agency.view_supplier', raise_exception=True)
#suppliers list
def suppliers_list(request):
    # Get the search query from the request, if provided
    query = request.GET.get('query', '')
    
    # Start with a query that fetches all suppliers or filters them based on the search query
    if query:
        suppliers = Supplier.objects.filter(
            Q(name__icontains=query) 
        )
    else:
        suppliers = Supplier.objects.all().order_by('created_at')
    
    # Set up pagination: Display 10 suppliers per page
    paginator = Paginator(suppliers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Render the suppliers list (filtered or unfiltered) to the template
    return render(request, 'Dashboard/suppliers/suppliers.html', {'page_obj': page_obj, 'query': query})




#suppliers update
@login_required
@permission_required('Agency.change_supplier', raise_exception=True)
def supplier_update(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    if request.method == 'POST':
        form = SupplierUpdateForm(request.POST, instance=supplier)
        if form.is_valid():
            updated_supplier = form.save(commit=False)
            updated_supplier.user = request.user
            updated_supplier.save()
            return redirect('suppliers_list') 
    else:
        form = SupplierUpdateForm(instance=supplier)
    context = {'form': form, 'supplier': supplier}
    return render(request, 'Dashboard/suppliers/supplier_update_form.html', context)









# booking registeration
@login_required
@permission_required('Agency.add_ticketbooking', raise_exception=True)
def ticket_register(request):
    if request.method == 'POST':
        form = BookingForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            Expense.objects.create(
                category='Other',
                amount=ticket.fare,
                description=f'Ticket booking fare for {ticket.passenger_name}',
                payment_method='evc_plus',
                date_created=timezone.now(),
                paid_by = request.user
                )
            messages.success(request, 'Ticket has been successfully registered.')
            return redirect('list_tickets') 
    else:
        form = BookingForm()

    context = {'form': form,
               'customers': Customer.objects.all(),
                'suppliers': Supplier.objects.all(),
                'city': City.objects.all()  }
    return render(request, 'Dashboard/tickets/add_ticket1.html', context)







# tickets list 
@login_required
@permission_required('Agency.view_ticketbooking', raise_exception=True)
def list_tickets(request):
    query = request.GET.get('query', '')
    if query:
        tickets = TicketBooking.objects.filter(
            Q(customer__name__icontains=query) | 
            Q(pnr__icontains=query) | 
            Q(destination__name__icontains=query)
        )
    else:
        tickets = TicketBooking.objects.annotate(
            total_price=ExpressionWrapper(
                Coalesce(F('fare'), 0) + Coalesce(F('commission'), 0) + Coalesce(F('tax'), 0),
                output_field=DecimalField()
            )
        ).order_by('-booking_date')
    
    # Set up pagination
    paginator = Paginator(tickets, 10)  # Shows 10 tickets per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj
    }
    return render(request, 'Dashboard/tickets/tickets.html', context)



# the update of ticket bookings
@login_required
@permission_required('Agency.change_ticketbooking', raise_exception=True)
def update_ticket(request, ticket_id):
    ticket = get_object_or_404(TicketBooking, pk=ticket_id)
    if request.method == 'POST':
        form = BookingForm(request.POST, request.FILES, instance=ticket)
        if form.is_valid():
            updated_ticket = form.save(commit=False)
            updated_ticket.user = request.user
            updated_ticket.save()
            if updated_ticket.status == 'canceled':
                # Handle transaction and payment adjustments
                with db_transaction.atomic():
                    adjust_financial_records_for_cancellation(updated_ticket)
                
                messages.info(request, f"All financial records for {updated_ticket.passenger_name} have been adjusted due to cancellation.")
            
            messages.success(request, 'Ticket booking updated successfully!')
            return redirect('list_tickets')
        else:
            print(form.errors)
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = BookingForm(instance=ticket)
    
    context = {
        'form': form,
        'ticket': ticket,
        'customers': Customer.objects.all(),
        'suppliers': Supplier.objects.all(),
        'city': City.objects.all()
    }
    return render(request, 'Dashboard/tickets/update_ticket.html', context)

def adjust_financial_records_for_cancellation(ticket):
    # Check if there's an associated transaction
    if ticket.transaction:
        transaction = ticket.transaction
        # Calculate amount to deduct (ticket fare + commission)
        amount_to_deduct = ticket.fare + ticket.commission

        # Adjust the transaction's paid and total amount
        with db_transaction.atomic():
            if transaction.paid_amount >= amount_to_deduct:
                transaction.paid_amount -= amount_to_deduct
            transaction.total_amount -= amount_to_deduct
            if transaction.total_amount < 0:
                transaction.total_amount = 0
            if transaction.paid_amount < 0:
                transaction.paid_amount = 0
            transaction.save()

            # If the transaction becomes zero or negative, consider changing its status
            if transaction.total_amount <= 0:
                transaction.status = 'pending'
            transaction.save()

            # Adjust payments linked to the transaction
            payments = Payment.objects.filter(transaction=transaction)
            for payment in payments:
                payment.amount -= amount_to_deduct
                if payment.amount < 0:
                    payment.amount = 0
                payment.save()

    # Adjust the expense record related to the ticket
    try:
        expense = Expense.objects.get(description=f'Ticket booking fare for {ticket.passenger_name}')
        expense.amount = 0  # Set the amount to zero instead of deleting the record
        description=f'Ticket booking fare for {ticket.passenger_name} is assigned 0 due to cancelation'
        expense.save()  # Save the updated expense record
    except Expense.DoesNotExist:
        pass  # No expense was found; ignore or log this as needed

    # Optionally, log this action
    ActivityLog.objects.create(
        user=ticket.user,
        action='cancel_ticket',
        content_type='TicketBooking',
        object_id=ticket.id,
        description=f'Cancellation processed for ticket of {ticket.passenger_name}'
    )







# visa lists to manage visa bookings
@login_required
@permission_required('Agency.view_visabooking', raise_exception=True)
def list_visa_bookings(request):
    query = request.GET.get('query', '')
    
    if query:
        visas = VisaBooking.objects.filter(
            Q(customer__name__icontains=query) | 
            Q(country__icontains=query)
        )
    else:
        visas = VisaBooking.objects.all()
    
    visas = visas.annotate(
        total_cost=ExpressionWrapper(
            F('visa_fee') + F('commission'),
            output_field=DecimalField()
        )
    )

    # Set up pagination
    paginator = Paginator(visas, 10)  # Display 10 visas per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj
    }
    return render(request, 'Dashboard/visas/visa_booking_list.html', context)



@login_required
@permission_required('Agency.add_city', raise_exception=True)
def city_register(request):
    if request.method == 'POST':
        form = cityForm(request.POST)
        if form.is_valid():
            new_city = form.save(commit=False)
            new_city.user = request.user
            new_city.save()
            redirect('cities')
    else:
        form = cityForm()
    return render(request,'Dashboard/city/city_regester.html')

@login_required
@permission_required('Agency.view_city', raise_exception=True)
def city_view(request):
    # Start with a query that fetches all cities
    query = request.GET.get('query', '')
    if query:
        cities = City.objects.filter(Q(name__icontains=query))
    else:
        cities = City.objects.all()

    # Set up pagination
    paginator = Paginator(cities, 10)  # Show 10 cities per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Render the city list to the template with pagination and the current query
    return render(request, 'Dashboard/city/manage_cities.html', {'page_obj': page_obj, 'query': query})





@login_required
@permission_required('Agency.change_city', raise_exception=True)
def city_update(request, id):
    city = get_object_or_404(City, id=id)
    if request.method == 'POST':
        form = cityForm(request.POST, instance=city)
        if form.is_valid():
            updated_city = form.save(commit=False)
            updated_city.user = request.user
            updated_city.save()
            return redirect('cities') 
    else:
        form = SupplierUpdateForm(instance=city)
    context = {'form': form, 'supplier': city}
    return render(request, 'Dashboard/city/city_update.html', context)







# visa booking regesteration 
@login_required
@permission_required('Agency.add_visabooking', raise_exception=True)
def visa_booking_register(request):
    customers = Customer.objects.all()
    if request.method == 'POST':
        form = VisaBookingForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the new visa booking to the database
            new_visa_booking = form.save(commit=False)
            new_visa_booking.user = request.user
            new_visa_booking.save()

            # You can add additional processing here if necessary
            new_visa_booking.save()

            Expense.objects.create(
                category='Other',
                amount=new_visa_booking.visa_fee,
                description=f'visa booking fee for {new_visa_booking.name}',
                payment_method='evc_plus',
                date_created=timezone.now(),
                paid_by = request.user
                )
            messages.success(request, 'Visa booking successfully created!')
            return redirect('visa_bookings_list') # Redirect to a new URL after success
    else:
        form = VisaBookingForm()

    return render(request, 'Dashboard/visas/visa_register.html', {
        'form': form,
        'customers':customers,
        'age_choices': VisaBooking.AGE_CHOICES,
    })







# the update function of visa bookings
@login_required
@permission_required('Agency.change_visabooking', raise_exception=True)
def update_visa_booking(request, id):
    visa = get_object_or_404(VisaBooking, pk=id)
    customers = Customer.objects.all()
    if request.method == 'POST':
        form = VisaBookingForm(request.POST, request.FILES, instance=visa)
        if form.is_valid():
            updated_visa =form.save(commit=False)
            updated_visa.user = request.user
            updated_visa.save()
            if updated_visa.status == 'canceled':
                # Handle transaction and payment adjustments
                with db_transaction.atomic():
                    adjust_financial_records_for_visa_cancellation(updated_visa)
            messages.success(request, 'Visa booking updated successfully!')
            return redirect('visa_bookings_list')  # Redirect to the visa booking listing page
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        form = VisaBookingForm(instance=visa)

    context = {
        'form': form,
        'visa': visa,
        'customers':customers,
        'age_choices': VisaBooking.AGE_CHOICES
    }
    return render(request, 'Dashboard/visas/visa_booking_update.html', context)





def adjust_financial_records_for_visa_cancellation(visa):
    # Check if there's an associated transaction
    if visa.transaction:
        transaction = visa.transaction
        # Calculate amount to deduct (ticket fare + commission)
        amount_to_deduct = visa.visa_fee + visa.commission

        # Adjust the transaction's paid and total amount
        with db_transaction.atomic():
            if transaction.paid_amount >= amount_to_deduct:
                transaction.paid_amount -= amount_to_deduct
            transaction.total_amount -= amount_to_deduct
            if transaction.total_amount < 0:
                transaction.total_amount = 0
            if transaction.paid_amount < 0:
                transaction.paid_amount = 0
            transaction.save()

            # If the transaction becomes zero or negative, consider changing its status
            if transaction.total_amount <= 0:
                transaction.status = 'pending'
            transaction.save()

            # Adjust payments linked to the transaction
            payments = Payment.objects.filter(transaction=transaction)
            for payment in payments:
                payment.amount -= amount_to_deduct
                if payment.amount < 0:
                    payment.amount = 0
                payment.save()

    # Adjust the expense record related to the ticket
    try:
        expense = Expense.objects.get(description=f'Ticket booking fare for {visa.name}')
        expense.amount = 0  # Set the amount to zero instead of deleting the record
        description=f'Ticket booking fare for {visa.name} is assigned 0 due to cancelation'
        expense.save()  # Save the updated expense record
    except Expense.DoesNotExist:
        pass  # No expense was found; ignore or log this as needed

    # then ticket cancelling log
    ActivityLog.objects.create(
        user=visa.user,
        action='cancel_ticket',
        content_type='TicketBooking',
        object_id=visa.id,
        description=f'Cancellation processed for ticket of {visa.name}'
    )








# the start of the invoice creation
@login_required
@permission_required('Agency.add_transaction', raise_exception=True)
def select_customer(request):
    customers = Customer.objects.all()
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        booking_type = request.POST.get('transaction_type')
        if booking_type == 'ticket':
            return redirect('customer_ticket_pending_bookings', customer_id=customer_id)
        elif booking_type == 'visa':
            return redirect('customer_pending_visa_bookings', customer_id=customer_id)
    return render(request, 'Dashboard/invoices/ticket_invoice_register.html', {'customers': customers})








@login_required
@permission_required('Agency.add_transaction', raise_exception=True)
def customer_ticket_pending_bookings(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    pending_ticket_bookings = TicketBooking.objects.filter(customer=customer, status='pending')

    if not pending_ticket_bookings.exists():
        no_pending_bookings = True
    else:
        no_pending_bookings = False

    # Calculate total cost for each booking
    for booking in pending_ticket_bookings:
        booking.total_cost = booking.fare + booking.commission
        

    total_costs = [booking.fare + booking.commission for booking in pending_ticket_bookings]
        
    b = sum(total_costs) 


    if request.method == 'POST':
        booking_form = BookingSelectionForm(request.POST)
        payment_form = PaymentForm(request.POST)
        if booking_form.is_valid() and payment_form.is_valid():
            selected_booking_ids = booking_form.cleaned_data['bookings']
            payment_method = payment_form.cleaned_data['payment_method']
            amount = payment_form.cleaned_data['paid_amount']

            selected_bookings = TicketBooking.objects.filter(id__in=selected_booking_ids)

            # Create a new transaction
            total_amount = sum(b.fare + b.commission for b in selected_bookings if b.status != 'cancelled')

            if amount > total_amount:
                messages.error(request, 'Paid amount cannot be greater than the total amount.')
                return render(request, 'Dashboard/invoices/ticket_customer_pending_booking.html', {
            'customer': customer,
            'pending_ticket_bookings': pending_ticket_bookings,
            'no_pending_bookings': no_pending_bookings,
            'booking_form': booking_form,
            'payment_form': payment_form,
            })

    

            with db_transaction.atomic():
                transaction = Transaction.objects.create(
                    customer=customer,
                    total_amount=total_amount,
                    transaction_type='ticket',
                    payment_method=payment_method,
                    paid_amount=amount,
                    user=request.user
                )

                Payment.objects.create(
                transaction=transaction,
                amount=amount,
                payment_method=payment_method,
                user=request.user
                 )

                for booking in selected_bookings:
                    if booking.status != 'cancelled':
                        booking.transaction = transaction
                        booking.status = 'confirmed'
                        booking.save()

                transaction.update_status()  # Update transaction based on payment made
                messages.success(request, 'Transaction successfully processed and payment recorded.')



                # Render the invoice as an HTML page
                context = { 
                    'customer_name': customer.name,
                    'customer_no': customer.phone,
                    'date': transaction.transaction_date.strftime('%d.%m.%Y'),
                    'invoice_no': transaction.reference_number,
                    'transaction_type': transaction.transaction_type,
                    'transaction_no': transaction.id,
                    'bookings': selected_bookings,
                    'subtotal': total_amount,
                    'partial': transaction.paid_amount,
                    'total': transaction.total_amount,
                    'remaining_amount' : total_amount - transaction.paid_amount,
                    'due_date':transaction.transaction_date,
                    'status':transaction.status,
                    'b':b,
                    'path_to_signature': '/path/to/your/signature.png'  # Update with the actual path to the signature
                }
                return render(request, 'Dashboard/invoices/ticket_invoice_template.html', context)
    else:
        booking_form = BookingSelectionForm()
        payment_form = PaymentForm()

    return render(request, 'Dashboard/invoices/ticket_customer_pending_booking.html', {
        'customer': customer,
        'pending_ticket_bookings': pending_ticket_bookings,
        'no_pending_bookings': no_pending_bookings,
        'booking_form': booking_form,
        'payment_form': payment_form,
    })





# invoices
@login_required
@permission_required('Agency.view_transaction', raise_exception=True)
def invoice_list(request):
    query = request.GET.get('query', '')
    if query:
        invoices = Transaction.objects.filter(
            Q(customer__name__icontains=query) | 
            Q(reference_number__icontains=query)
        )
    else:
        invoices = Transaction.objects.all()

    # Pagination setup
    paginator = Paginator(invoices, 10)  # Display 10 invoices per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'Dashboard/invoices/invoice_list.html', {'page_obj': page_obj})





# the view of all invoices
@login_required
@permission_required('Agency.view_transaction', raise_exception=True)
def view_invoices(request, invoice_id):
    invoice = get_object_or_404(Transaction, id=invoice_id)
    
    if invoice.transaction_type == 'ticket':
        selected_bookings = TicketBooking.objects.filter(transaction=invoice)
        subtotal = sum(b.fare + b.commission if b.status != 'canceled' else 0 for b in selected_bookings)
        for booking in selected_bookings:
            if booking.status != 'canceled':
                booking.total_cost = booking.fare + booking.commission 
            else:
                booking.total_cost = 0


    elif invoice.transaction_type == 'visa':
        selected_bookings = VisaBooking.objects.filter(transaction=invoice)
        subtotal = sum(booking.visa_fee + booking.commission for booking in selected_bookings)
        for booking in selected_bookings:
            if booking.status != 'canceled':
                booking.total_cost = booking.visa_fee + booking.commission 
            else:
                booking.total_cost = 0
    
   

    remaining_amount = subtotal - invoice.paid_amount
    if remaining_amount < 0:
        remaining_amount = 0 
    
    context = {
        'invoice': invoice,
        'customer_name': invoice.customer.name,
        'customer_no': invoice.customer.phone,
        'due_date': invoice.transaction_date.strftime('%d.%m.%Y'),
        'invoice_no': invoice.reference_number,
        'transaction_type': invoice.transaction_type,
        'transaction_no': invoice.id,
        'bookings': selected_bookings,
        'subtotal': subtotal,
        'partial': invoice.paid_amount,
        'remaining': remaining_amount,
        'total': invoice.total_amount,
        'status':invoice.status,
        'path_to_signature': '/path/to/your/signature.png',  # Update with the actual path to the signature
        'logo_url': '/path/to/your/logo.png'  # Update with the actual path to the logo
    }

    if invoice.transaction_type == 'ticket':
        return render(request, 'Dashboard/invoices/ticket_invoice_template.html', context)
    elif invoice.transaction_type == 'visa':
        return render(request, 'Dashboard/invoices/visa_invoice_template.html', context)









# the completion of transaction if it is have 
@login_required
@permission_required('Agency.add_transaction', raise_exception=True)
def incomplete_transactions(request):
    transactions = Transaction.objects.annotate(
        remaining=ExpressionWrapper(F('total_amount') - F('paid_amount'), output_field=DecimalField())
    ).filter(remaining__gt=0)
    
    return render(request, 'Dashboard/invoices/ticket_incomplete_transactions.html', {'transactions': transactions})


@login_required
@permission_required('Agency.add_transaction', raise_exception=True)
def complete_payment(request, transaction_id):
     
     transaction = get_object_or_404(Transaction, id=transaction_id)
     previous_payments = Payment.objects.filter(transaction=transaction)
    
     if request.method == 'POST':
        payment_form = CompletePaymentForm(request.POST)
        if payment_form.is_valid():
            amount = payment_form.cleaned_data['amount']
            payment_method = payment_form.cleaned_data['payment_method']
            remaining = transaction.total_amount - transaction.paid_amount

            if amount > remaining:
                messages.error(request, 'Paid amount cannot be greater than the remaining amount.')
                return render(request, 'Dashboard/invoices/ticket_complete_payment.html', {
                    'transaction': transaction,
                    'previous_payments': previous_payments,
                    'payment_form': payment_form,
                    'remaining_amount': transaction.total_amount - transaction.paid_amount,
                })
            
            with db_transaction.atomic():

                # Create a new payment record
                Payment.objects.create(
                    transaction=transaction,
                    amount=amount,
                    payment_method=payment_method,
                    user=request.user 
                )
                
                # Update the transaction
                transaction.paid_amount += amount
                transaction.update_status()
                if transaction.paid_amount >= transaction.total_amount:
                        transaction.status = 'paid'
                        transaction.save()

                
                return redirect('view_invoice', invoice_id=transaction.id)
     else:
        payment_form = CompletePaymentForm()
    
     # Determine which template to use based on the transaction type
     if transaction.transaction_type == 'ticket':
        template_name = 'Dashboard/invoices/ticket_complete_payment.html'
     elif transaction.transaction_type == 'visa':
        template_name = 'Dashboard/invoices/visa_complete_payment.html'
     return render(request, 'Dashboard/invoices/ticket_complete_payment.html', {
        'transaction': transaction,
        'previous_payments': previous_payments,
        'payment_form': payment_form,
        'remaining_amount': transaction.total_amount - transaction.paid_amount,
     })









@login_required
@permission_required('Agency.add_transaction', raise_exception=True)
def customer_pending_visa_bookings(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    pending_visa_bookings = VisaBooking.objects.filter(customer=customer, status='pending')

    if not pending_visa_bookings.exists():
        no_pending_bookings = True
    else:
        no_pending_bookings = False


    for booking in pending_visa_bookings:
        booking.total_cost = booking.visa_fee + booking.commission

    if request.method == 'POST':
        booking_form = BookingSelectionForm(request.POST, transaction_type='visa')
        payment_form = PaymentForm(request.POST)
        if booking_form.is_valid() and payment_form.is_valid():
            selected_booking_ids = booking_form.cleaned_data['bookings'].values_list('id', flat=True)
            payment_method = payment_form.cleaned_data['payment_method']
            amount = payment_form.cleaned_data['paid_amount']

            selected_bookings = VisaBooking.objects.filter(id__in=selected_booking_ids)
            total_amount = sum(b.visa_fee + b.commission for b in selected_bookings)
            if amount > total_amount:
                messages.error(request, 'Paid amount cannot be greater than the total amount.')
                return render(request, 'Dashboard/invoices/visa_customer_pending_booking.html', {
                    'customer': customer,
                    'pending_visa_bookings': pending_visa_bookings,
                    'no_pending_bookings': no_pending_bookings,
                    'booking_form': booking_form,
                    'payment_form': payment_form,
                })

            with db_transaction.atomic():
                # Create a new transaction
                transaction = Transaction.objects.create(
                    customer=customer,
                    total_amount=total_amount,
                    transaction_type='visa',
                    payment_method=payment_method,
                    paid_amount=amount,
                    user = request.user
                )

                # Create a new payment record
                Payment.objects.create(
                    transaction=transaction,
                    amount=amount,
                    payment_method=payment_method,
                    user = request.user
                )

                # Associate bookings with the transaction and update their status
                for booking in selected_bookings:
                    booking.transaction = transaction
                    booking.status = 'confirmed'
                    booking.save()

                # Update transaction status based on paid amount
                transaction.update_status()

                # Render the invoice as an HTML page
                context = {
                    'customer_name': customer.name,
                    'customer_no': customer.phone,
                    'date': transaction.transaction_date.strftime('%d.%m.%Y'),
                    'invoice_no': transaction.reference_number,
                    'transaction_type': transaction.transaction_type,
                    'transaction_no': transaction.id,
                    'bookings': selected_bookings,
                    'subtotal': total_amount,
                    'partial': transaction.paid_amount,
                    'total': transaction.total_amount,
                    'remaining_amount': total_amount - transaction.paid_amount,
                    'path_to_signature': '/path/to/your/signature.png'  # Update with the actual path to the signature
                }

                return render(request, 'Dashboard/invoices/visa_invoice_template.html', context)
    else:
        booking_form = BookingSelectionForm(transaction_type='visa')
        payment_form = PaymentForm()

    return render(request, 'Dashboard/invoices/visa_customer_pending_booking.html', {
        'customer': customer,
        'pending_visa_bookings': pending_visa_bookings,
        'no_pending_bookings': no_pending_bookings,
        'booking_form': booking_form,
        'payment_form': payment_form,
    })










# the regesteration of the employee
@login_required
@permission_required('Agency.add_employee', raise_exception=True)
def register_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee registered successfully!')
            return redirect('employee_list')  # Redirect to a success page or another relevant page
    else:
        form = EmployeeForm()

    return render(request, 'Dashboard/HR/employee_register.html', {'form': form})






# list of the employees to manage
@login_required
@permission_required('Agency.view_employee', raise_exception=True)
def employee_list(request):
    search_query = request.GET.get('search', '')  # Get the search parameter from the URL
    if search_query:
        employees = Employee.objects.filter(
            Q(name__icontains=search_query) |
            Q(user__username__icontains=search_query)|
            Q(phone__icontains=search_query)   # Assuming 'user' is a related field for username
        )
    else:
        employees = Employee.objects.all()

    # Set up pagination
    paginator = Paginator(employees, 10)  # Shows 10 employees per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj
    }
    return render(request, 'Dashboard/HR/manage_employees.html', context)







@login_required
@permission_required('Agency.change_employee', raise_exception=True)
def employee_update(request, employee_id=None):
    if employee_id:
        employee = get_object_or_404(Employee, pk=employee_id)
        form = EmployeeForm(request.POST or None, request.FILES or None, instance=employee)
    else:
        form = EmployeeForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if form.is_valid():
            updated_employee = form.save()
            updated_employee.user = request.user
            updated_employee.save()
            messages.success(request, 'Expense record regestered successfully!')
            return redirect('employee_list')  # Redirect to the employee list view

    return render(request, 'Dashboard/HR/employee_update.html', {'form': form, 'employee': employee if employee_id else None})






# the list of expense
@login_required
@permission_required('Agency.view_expense', raise_exception=True)
def expense_list(request):
    query = request.GET.get('query', '')
    if query:
        expenses = Expense.objects.filter(
            Q(category__icontains=query) |
            Q(description__icontains=query) |
            Q(amount__icontains=query)  # Note: filtering by amount might need exact matches unless amount is a CharField
        )
    else:
        expenses = Expense.objects.all()

    # Set up pagination
    paginator = Paginator(expenses, 10)  # Shows 10 expenses per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'Dashboard/expenses/expenses.html', {'page_obj': page_obj})




# expense record regesteration
@login_required
@permission_required('Agency.add_expense', raise_exception=True)
def record_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            new_exepense = form.save(commit= False)
            new_exepense.paid_by = request.user
            new_exepense.save()
            
            return redirect('expenses')
    else:
        form = ExpenseForm()

    payment_methods = Transaction.PAYMENT_METHOD_CHOICES
    Expense_category = Expense.EXPENSE_CATEGORY_CHOICES
    context = {'form': form,
               'payment_methods':payment_methods,
               'Expense_category': Expense_category,}

    return render(request, 'Dashboard/expenses/expense_payments.html',context )







# the update of the expense
@login_required
@permission_required('Agency.change_expense', raise_exception=True)
def expense_update(request, expense_id):
    expense = get_object_or_404(Expense, pk=expense_id)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            updated_expense = form.save(commit=False)
            updated_expense.user = request.user
            updated_expense.save()
            messages.success(request, 'Expense record updates successfully!')
            return redirect('expenses') 
        else:
            print("Form is not valid")  # Check what's not valid
            print(form.errors) 
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'Dashboard/expenses/expense_payments_update.html',{'form': form})







@login_required
@permission_required('Agency.add_asset', raise_exception=True)
def register_asset(request):
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            new_asset = form.save(commit=False)
            new_asset.user = request.user
            new_asset.save()
            messages.success(request, 'Asset  regestered successfully!')
            return redirect('list_assets')
            
        
    else:
        form = AssetForm()  # An unbound form

    return render(request, 'Dashboard/purchase_assets/asset_register.html', {'form': form})







@login_required
@permission_required('Agency.view_asset', raise_exception=True)
def list_assets(request):
    query = request.GET.get('query', '')
    if query:
        assets = Asset.objects.filter(
            Q(asset_name__icontains=query) |
            Q(description__icontains=query) |
            Q(user__username__icontains=query)
        )
    else:
        assets = Asset.objects.all()

    return render(request, 'Dashboard/purchase_assets/manage_assets.html', {'assets': assets})







@login_required
@permission_required('Agency.change_asset', raise_exception=True)
def update_asset(request, id):
    asset = get_object_or_404(Asset, pk=id)
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            updated_asset = form.save(commit=False)
            updated_asset.user = request.user
            updated_asset.save()
            messages.success(request, 'Asset record updates successfully!')
            return redirect('list_assets')  # Redirect to the asset listing page
    else:
        form = AssetForm(instance=asset)
    
    return render(request, 'Dashboard/purchase_assets/update_asset.html', {'form': form})






def get_current_year_range():
    today = timezone.now()
    return (timezone.make_aware(datetime(today.year, 1, 1)), 
            timezone.make_aware(datetime(today.year + 1, 1, 1)))
# the dashboard home pahe
@login_required
def index(request):
    today = timezone.now()
    first_day_of_current_month = timezone.make_aware(datetime(today.year, today.month, 1))
    last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_last_month = timezone.make_aware(datetime(last_day_of_last_month.year, last_day_of_last_month.month, 1))
    current_year_start, current_year_end = get_current_year_range()



    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_indices = {month: index for index, month in enumerate(months)}

    # Initialize sums for each month
    expenses_values = [0.00] * 12
    revenues_values = [0.00] * 12

    # Query and annotate data by month
    monthly_expenses = Expense.objects.filter(date_created__range=[current_year_start, current_year_end]) \
                                       .annotate(month=TruncMonth('date_created')) \
                                       .values('month') \
                                       .annotate(total=Sum('amount')) \
                                       .order_by('month')

    monthly_revenues = Transaction.objects.filter(transaction_date__range=[current_year_start, current_year_end]) \
                                          .annotate(month=TruncMonth('transaction_date')) \
                                          .values('month') \
                                          .annotate(total=Sum('total_amount')) \
                                          .order_by('month')

    # Assign fetched data to corresponding months
    for expense in monthly_expenses:
        month_str = expense['month'].strftime('%b')
        if month_str in month_indices:
            expenses_values[month_indices[month_str]] = float(expense['total'] or 0)

    for revenue in monthly_revenues:
        month_str = revenue['month'].strftime('%b')
        if month_str in month_indices:
            revenues_values[month_indices[month_str]] = float(revenue['total'] or 0)



    # Current month's filters
    current_month_filter = {'transaction_date__range': [first_day_of_current_month, today]}
    last_month_filter = {'transaction_date__range': [first_day_of_last_month, last_day_of_last_month]}

    # Revenue and Expenses aggregates
    current_month_revenues = Transaction.objects.filter(**current_month_filter).aggregate(
        total=Sum('total_amount', output_field=DecimalField())
    )['total'] or Decimal(0)

    last_month_revenues = Transaction.objects.filter(**last_month_filter).aggregate(
        total=Sum('total_amount', output_field=DecimalField())
    )['total'] or Decimal(0)

    current_month_expenses = Expense.objects.filter(
        date_created__range=[first_day_of_current_month, today]
    ).aggregate(total=Sum('amount', output_field=DecimalField()))['total'] or Decimal(0)

    last_month_expenses = Expense.objects.filter(
        date_created__range=[first_day_of_last_month, last_day_of_last_month]
    ).aggregate(total=Sum('amount', output_field=DecimalField()))['total'] or Decimal(0)

    # Aggregations for tickets and visas
    ticket_data_current = TicketBooking.objects.filter(
        travel_date__range=[first_day_of_current_month, today], status='confirmed'
    ).aggregate(
        total_commission=Sum('commission', output_field=DecimalField()),
        total_fare=Sum('fare', output_field=DecimalField())
    )

    visa_data_current = VisaBooking.objects.filter(
        departure_date__range=[first_day_of_current_month, today], status='confirmed'
    ).aggregate(
        total_commission=Sum('commission', output_field=DecimalField()),
        total_visa_fee=Sum('visa_fee', output_field=DecimalField())
    )

    ticket_data_last = TicketBooking.objects.filter(
        travel_date__range=[first_day_of_last_month, last_day_of_last_month], status='confirmed'
    ).aggregate(
        total_commission=Sum('commission', output_field=DecimalField()),
        total_fare=Sum('fare', output_field=DecimalField())
    )

    visa_data_last = VisaBooking.objects.filter(
        departure_date__range=[first_day_of_last_month, last_day_of_last_month], status='confirmed'
    ).aggregate(
        total_commission=Sum('commission', output_field=DecimalField()),
        total_visa_fee=Sum('visa_fee', output_field=DecimalField())
    )

    # Handling possible None values by ensuring Decimal defaults
    total_current_month_commission = (ticket_data_current['total_commission'] or Decimal(0)) + (visa_data_current['total_commission'] or Decimal(0))
    total_current_month_fare = (ticket_data_current['total_fare'] or Decimal(0)) + (visa_data_current['total_visa_fee'] or Decimal(0))
    total_last_month_commission = (ticket_data_last['total_commission'] or Decimal(0)) + (visa_data_last['total_commission'] or Decimal(0))
    total_last_month_fare = (ticket_data_last['total_fare'] or Decimal(0)) + (visa_data_last['total_visa_fee'] or Decimal(0))

    revenue_change = current_month_revenues - last_month_revenues
    percentage_change = (revenue_change / last_month_revenues * 100) if last_month_revenues else 0


    total_customers = Customer.objects.all().count

    # this_month_revenue = total_current_month_fare + total_current_month_commission

    # last_month_revenue = total_last_month_commission + total_last_month_fare


    # revenue_change = this_month_revenue - last_month_revenue

    # percentage_change = (revenue_change / last_month_revenues * 100) if last_month_revenues else 0


    # the destination of cities
    top_ticket_destinations = TicketBooking.objects.filter(
        travel_date__range=[first_day_of_current_month, today],
        status='confirmed'
    ).values('destination__name').annotate(
        count=Count('id')
    ).order_by('-count')

    top_ticket_origin = TicketBooking.objects.filter(
        travel_date__range=[first_day_of_current_month, today],
        status='confirmed'
    ).values('from_city__name').annotate(
        count=Count('id')
    ).order_by('-count')




    payment_methods_counts = Payment.objects.values('payment_method').annotate(total=Count('payment_method')).order_by()
    total_payments = sum(payment['total'] for payment in payment_methods_counts)

    # Preparing data for the chart with percentage calculations
    payment_labels = [payment['payment_method'] for payment in payment_methods_counts]
    payment_values = [(payment['total'] / total_payments * 100) if total_payments > 0 else 0 for payment in payment_methods_counts]

    invoices = Transaction.objects.order_by('-transaction_date')[:5]

    print(months)
    print(expenses_values)
    print(f"Current Month Revenues: {current_month_revenues}")
    print(f"Last Month Revenues: {last_month_revenues}")
    print(f"Current Month Expenses: {current_month_expenses}")
    print(f"Last Month Expenses: {last_month_expenses}")


    context = {
        'total_revenue_current': current_month_revenues,
        'total_expenses_current': current_month_expenses,
        'total_commission_current': total_current_month_commission,
        'total_fare_current': total_current_month_fare,
        'total_revenue_last': last_month_revenues,
        'total_expenses_last': last_month_expenses,
        'total_commission_last': total_last_month_commission,
        'total_fare_last': total_last_month_fare,
        'total_customers':total_customers,
        'percentage_change':percentage_change,
        'top_ticket_destinations':top_ticket_destinations,
        'top_ticket_origin':top_ticket_origin,
        'invoices':invoices,
        'payment_labels': payment_labels,
        'payment_values': payment_values,
        'months':months,
        'expenses_values':expenses_values,
        'revenues_values':revenues_values,


    }

    return render(request, 'Dashboard/index.html', context)


# def homepage(request):
#     return render(request,'Dashboard/index1.html')







@login_required
@permission_required('Agency.view_visabooking', raise_exception=True)
@permission_required('Agency.view_ticketbooking', raise_exception=True)
def booking_report(request): 
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')

    context = {
        'ticket_bookings': [],
        'visa_bookings': [],
        'total_fares': 0,
        'total_commissions': 0,
        'start_date':start_date,
        'end_date':end_date,
    }
    print(context)

    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        ticket_bookings = TicketBooking.objects.filter(travel_date__range=(start_date, end_date))
        for booking in ticket_bookings:
            booking.total_cost = booking.fare + booking.commission
        visa_bookings = VisaBooking.objects.filter(departure_date__range=(start_date, end_date))
    else:
        ticket_bookings = TicketBooking.objects.all()
        visa_bookings = VisaBooking.objects.all()

    # Calculating totals
    context['ticket_bookings'] = ticket_bookings
    context['visa_bookings'] = visa_bookings
    context['total_fares'] = sum(b.fare for b in ticket_bookings) + sum(b.visa_fee for b in visa_bookings)
    context['total_commissions'] = sum(b.commission for b in ticket_bookings) + sum(b.commission for b in visa_bookings)
   
 
    return render(request,'Dashboard/Reports/Booking_reports.html',context)






@login_required
@permission_required('Agency.add_expense', raise_exception=True)
def expense_report(request):
    # Extract dates from GET parameters
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')

    # Convert string dates to date objects
    start_date = parse_date(start_date) if start_date else None
    end_date = parse_date(end_date) if end_date else None

    # Initialize the query to fetch all expenses or within date range if specified
    if start_date and end_date:
        expenses = Expense.objects.filter(date_created__date__range=(start_date, end_date))
    else:
        expenses = Expense.objects.all()

    return render(request, 'Dashboard/Reports/expense_report.html', {
        'expenses': expenses,
        'start_date': start_date,
        'end_date': end_date
    })






# the customer report
@login_required
@permission_required('Agency.add_customer', raise_exception=True)
def customer_report(request):
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')
    search_query = request.GET.get('search', '')


    customers = Customer.objects.all()
    if search_query:
         customers = customers.filter(
            Q(phone__icontains=search_query) | 
            Q(name__icontains=search_query) 
        )

    if start_date and end_date:
        customers = customers.annotate(
            total_paid=Sum('transaction__payment__amount',
                           filter=Q(transaction__transaction_date__range=[start_date, end_date])
                          )
        ).order_by('-total_paid') 
    else:
        # Calculate total paid amount regardless of the date if no date range is specified
        customers = customers.annotate(
            total_paid=Sum('transaction__payment__amount')
        ).order_by('-total_paid') 

    return render(request, 'Dashboard/Reports/customer_report.html', {
        'customers': customers,
        'start_date': start_date,
        'end_date': end_date
    })






# the supplier report
@login_required
@permission_required('Agency.add_supplier', raise_exception=True)
def supplier_report(request):
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')
    search_query = request.GET.get('search', '')

    suppliers = Supplier.objects.all()

    if search_query:
        suppliers = suppliers.filter(name__icontains =search_query)

    if start_date and end_date:
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)
        suppliers = suppliers.annotate(
            total_fare=Sum('ticketbooking__fare',
                           filter=~Q(ticketbooking__status='canceled') &
                                  Q(ticketbooking__booking_date__range=[start_date, end_date])
                           )
        ).order_by('-total_fare')


    else:
        suppliers = suppliers.annotate(
            total_fare=Sum('ticketbooking__fare',
                           filter=~Q(ticketbooking__status='canceled') 
                           )
        ).order_by('-total_fare')

    return render(request, 'Dashboard/Reports/supplier_report.html', {
        'suppliers': suppliers,
        'start_date': start_date,
        'end_date': end_date
    })






def departure_report(request):
    search_query = request.GET.get('search', '')
    departure_date = request.GET.get('startDate', '')

    departures = TicketBooking.objects.all()

    if search_query:
        departures = departures.filter(destination__name__icontains=search_query)

    if departure_date:
        departures = departures.filter(travel_date=departure_date)

    context = {
        'departures': departures,
        'search_query': search_query,
        'departure_date': departure_date,
        'today': timezone.now(),
    }
    return render(request, 'Dashboard/Reports/departure_report.html', context)








@login_required
@permission_required('Agency.add_visabooking', raise_exception=True)
def sales_report(request):
    start_date = request.GET.get('startDate', timezone.now().date())
    end_date = request.GET.get('endDate', timezone.now().date())

    # Fetch and annotate ticket bookings within the date range
    tickets = TicketBooking.objects.filter(
        booking_date__range=[start_date, end_date]
    ).annotate(
        transaction_type=Value('Ticket', output_field=CharField()),
        date=F('booking_date'),
        amount=ExpressionWrapper(F('fare') + F('commission'), output_field=DecimalField())
    ).values(
        'id', 'date', 'customer__name', 'transaction_type', 'amount', 'user__username'
    )

    # Fetch and annotate visa bookings within the date range
    visas = VisaBooking.objects.filter(
        date_created__range=[start_date, end_date]
    ).annotate(
        transaction_type=Value('Visa', output_field=CharField()),
        date=F('date_created'),
        amount=ExpressionWrapper(F('visa_fee') + F('commission'), output_field=DecimalField())
    ).values(
        'id', 'date', 'customer__name', 'transaction_type', 'amount', 'user__username'
    )

    # Combine the two querysets
    from itertools import chain
    transactions = list(chain(tickets, visas))

    # Sort transactions by the common date key
    transactions.sort(key=lambda x: x['date'])


    return render(request, 'Dashboard/Reports/sales_report.html', {
        'transactions': transactions,
        'start_date': start_date,
        'end_date': end_date
    })


@login_required
@permission_required('Agency.view_assets', raise_exception=True)
def assets_report(request):
    # Fetch dates from GET request or use default values
    start_date = request.GET.get('startDate', datetime.today().strftime('%Y-%m-%d'))
    end_date = request.GET.get('endDate', datetime.today().strftime('%Y-%m-%d'))

    # Convert string dates to datetime objects
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Filter assets based on the provided date range
    assets = Asset.objects.filter(purchase_date__range=[start_date, end_date])

    return render(request, 'Dashboard/Reports/assets_report.html', {
        'assets': assets,
        'start_date': start_date,
        'end_date': end_date
    })











@login_required
@permission_required('Agency.view_customuser', raise_exception=True)
def income_statement(request):
    # Default to the current month's first and last day if no dates are provided
    start_date = request.GET.get('startDate', datetime.now().strftime('%Y-%m-01'))
    end_date = request.GET.get('endDate', datetime.now().strftime('%Y-%m-%d'))

    # Ensure the dates are in the correct format
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    # Filter transactions and expenses by the provided date range
    transactions = Transaction.objects.filter(transaction_date__date__range=[start_date, end_date])
    expenses = Expense.objects.filter(date_created__date__range=[start_date, end_date])

    # Sum up revenues based on transaction type
    total_ticket_sales = transactions.filter(transaction_type='ticket').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_visa_fees = transactions.filter(transaction_type='visa').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_revenues = total_ticket_sales + total_visa_fees

    # Sum up expenses
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    # Calculate net income
    net_income = total_revenues - total_expenses

    context = {'start_date': start_date,
                'end_date': end_date,
                'total_ticket_sales': total_ticket_sales,
                'total_visa_fees': total_visa_fees,
                'total_revenues': total_revenues,
                'total_expenses': total_expenses,
                'net_income': net_income}

    return render(request,'Dashboard/Reports/income_statement.html',context)














