from datetime import date, datetime, timedelta, timezone
from django.shortcuts import render,get_object_or_404,redirect
from django.db.models import Q, Count, Sum


from django.core.paginator import Paginator
from Agency import models
from Agency.forms import AssetForm, BookingForm, BookingSelectionForm, CompletePaymentForm, CustomerRegistrationForm, CustomerUpdateForm, DateSelectionForm, EmployeeForm, ExpenseForm, PaymentForm, SupplierRegistrationForm, SupplierUpdateForm,   VisaBookingForm, cityForm
from Agency.models import Asset, City, Country,  Customer, Employee, Expense, Payment, Supplier, TicketBooking, Transaction, VisaBooking 
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

from django.contrib.contenttypes.models import ContentType

from Users.utils import log_error
from itertools import chain



@login_required
@permission_required('Agency.view_customer', raise_exception=True)
def customers_list(request):
    try:
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
    except Exception as e:
        log_error(request, e)
        messages.error(request, 'An unexpected error occurred. Please try again.')
        return render(request, 'Dashboard/customers/customers.html', {'page_obj': [], 'query': query})








# the customers registeration function 
@login_required
@permission_required('Agency.add_customer', raise_exception=True)
def customer_registration(request):
    try:
        if request.method == 'POST':
            form = CustomerRegistrationForm(request.POST)
            if form.is_valid():
                new_customer = form.save(commit=False)
                new_customer.user = request.user
                new_customer.save()
                messages.success(request, 'Customer registered successfully!')
                return redirect('customers')
            else:
                messages.error(request, 'Please correct the error below.')
        else:
            form = CustomerRegistrationForm()
        return render(request, 'Dashboard/customers/customer_register.html', {'form': form})
    except Exception as e:
        log_error(request, e)
        messages.error(request, 'An unexpected error occurred. Please try again.')
        return render(request, 'Dashboard/customers/customer_register.html', {'form': form})






#customers update 
@login_required
@permission_required('Agency.change_customer', raise_exception=True)
def customer_update(request, id):
    try:
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

        context = {
            'form': form,
            'customer': customer
        }
        return render(request, 'Dashboard/customers/customer_update_form.html', context)
    except Exception as e:
        log_error(request, e)
        messages.error(request, 'An unexpected error occurred. Please try again.')
        return render(request, 'Dashboard/customers/customer_update_form.html', context)






# supplier registeration 
@login_required
@permission_required('Agency.add_supplier', raise_exception=True)
def supplier_registration(request):
    try:
        if request.method == 'POST':
            form = SupplierRegistrationForm(request.POST)
            if form.is_valid():
                new_supplier = form.save(commit=False)
                new_supplier.user = request.user
                new_supplier.save()
                messages.success(request, 'Supplier registered successfully!')

                return redirect('suppliers_list')
        else:
            form = SupplierRegistrationForm()

        context = {
            'form': form
        }
        return render(request, 'Dashboard/suppliers/supplier_registration.html', context)
    except Exception as e:
        log_error(request, e)
        return render(request, 'Dashboard/suppliers/supplier_registration.html', context)





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
        ).order_by('-created_at')
    else:
        suppliers = Supplier.objects.all().order_by('-created_at')
    
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
    try:
        supplier = get_object_or_404(Supplier, id=id)
        if request.method == 'POST':
            form = SupplierUpdateForm(request.POST, instance=supplier)
            if form.is_valid():
                updated_supplier = form.save(commit=False)
                updated_supplier.user = request.user
                updated_supplier.save()
                messages.success(request, 'supplier updated successfully!')

                return redirect('suppliers_list')
        else:
            form = SupplierUpdateForm(instance=supplier)
        context = {'form': form, 'supplier': supplier}
        return render(request, 'Dashboard/suppliers/supplier_update_form.html', context)
    except Exception as e:
        log_error(request, e)
        return render(request, 'Dashboard/suppliers/supplier_update_form.html', context)








# booking registeration
@login_required
@permission_required('Agency.add_ticketbooking', raise_exception=True)
def ticket_register(request):
    try:

        if request.method == 'POST':
            form = BookingForm(request.POST, request.FILES)
            if form.is_valid():
                ticket = form.save(commit=False)
                ticket.user = request.user
                ticket.save()
                Expense.objects.create(
                    category='Other',
                    amount=ticket.fare,
                    description=f'Ticket booking fare for {ticket.id} {ticket.passenger_name}',
                    payment_method='evc_plus',
                    date_created=timezone.now(),
                    paid_by = request.user
                    )
                messages.success(request, 'Ticket has been successfully registered.')
                return redirect('list_tickets') 
        else:
            form = BookingForm()
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred during ticket registration.")
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
    try:
        query = request.GET.get('query', '')
        if query:
            tickets = TicketBooking.objects.filter(
                Q(customer__name__icontains=query) |
                Q(pnr__icontains=query) |
                Q(destination__name__icontains=query)
            ).annotate(
                total_price=ExpressionWrapper(
                    F('fare') + F('commission') + F('tax'),
                    output_field=DecimalField()
                )
            )
        else:
            tickets = TicketBooking.objects.annotate(
                total_price=ExpressionWrapper(
                    F('fare') + F('commission') + F('tax'),
                    output_field=DecimalField()
                )
            ).order_by('-booking_date')
        
        paginator = Paginator(tickets, 10)  # Shows 10 tickets per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {'page_obj': page_obj}
        return render(request, 'Dashboard/tickets/tickets.html', context)
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while fetching the ticket list.")
        return render(request, 'Dashboard/tickets/tickets.html', {'page_obj': None})

# the update of ticket bookings
@login_required
@permission_required('Agency.change_ticketbooking', raise_exception=True)
def adjust_financial_records_for_cancellation(ticket, request):
    try:
        with db_transaction.atomic():
            if ticket.transaction:
                transaction = ticket.transaction
                amount_to_deduct = ticket.fare + ticket.commission
                new_total_amount = max(transaction.total_amount - amount_to_deduct, 0)
                transaction.total_amount = new_total_amount
                adjust_payments(transaction)
                ticket.transaction = None
                ticket.save()
                transaction.update_status()
            update_expense_record(ticket)
            log_action(request, ticket)
            messages.info(request, f"All financial records for {ticket.passenger_name} have been adjusted due to cancellation.")
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while adjusting financial records.")




def adjust_payments(transaction,request):
    try:

        payments = Payment.objects.filter(transaction=transaction).order_by('-payment_date')
        total_paid = sum(payment.amount for payment in payments)

        # Calculate the effective amount to adjust (if total paid is greater than the new total amount)
        if total_paid > transaction.total_amount:
            excess_payment = total_paid - transaction.total_amount
            for payment in payments:
                if excess_payment <= 0:
                    break
                possible_reduction = min(payment.amount, excess_payment)
                payment.amount -= possible_reduction
                payment.save()
                excess_payment -= possible_reduction

        # Update the transaction's paid amount and save the transaction
        transaction.paid_amount = sum(p.amount for p in Payment.objects.filter(transaction=transaction))
        transaction.save()
        transaction.update_status()
    except Exception as e:
        log_error(request, e)


def update_expense_record(ticket,request):
    try:
        expense = Expense.objects.get(description=f'Ticket booking fare for {ticket.id} {ticket.passenger_name}')
        expense.amount = 0  # Set the amount to zero instead of deleting the record
        expense.save()
    except Expense.DoesNotExist:
        # Handle the case where there is no existing expense
        Expense.objects.create(
            description=f'Ticket booking fare for {ticket.id} {ticket.passenger_name}',
            amount=0
        )
    except Exception as e:
        log_error(request, e)


def back_to_pending(ticket, request):
    try:

        
        # Retrieve the existing expense record for the ticket
        expense = Expense.objects.get(description=f'Ticket booking fare for {ticket.id} {ticket.passenger_name}')
        # Update the amount to the ticket's fare
        expense.amount = ticket.fare
        expense.save()
        messages.info(request, f"Financial records for {ticket.passenger_name} have been adjusted back to pending status.")
        print(f"Updated existing expense record for {ticket.passenger_name} with amount {ticket.fare}")
    except Expense.DoesNotExist:
        #Create a new expense record if it doesn't exist
        Expense.objects.create(
            description=f'Ticket booking fare for {ticket.id} {ticket.passenger_name}',
            amount=ticket.fare
        )
        messages.info(request, f"New financial record created for {ticket.passenger_name} as the ticket status is set back to pending.")
        print(f"Created new expense record for {ticket.passenger_name} with amount {ticket.fare}")
    except Exception as e:
        log_error(request, e)

def update_ticket(request, ticket_id):
    try:
        ticket = get_object_or_404(TicketBooking, pk=ticket_id)
        previous_status = ticket.status  # Track the previous status
        if request.method == 'POST':
            form = BookingForm(request.POST, request.FILES, instance=ticket)
            if form.is_valid():
                updated_ticket = form.save(commit=False)
                updated_ticket.user = request.user
                updated_ticket.save()
                if updated_ticket.status == 'canceled':
                    adjust_financial_records_for_cancellation(updated_ticket, request)
                elif updated_ticket.status == 'pending' and previous_status == 'canceled':
                    # Reverse the cancellation effects on the expense record
                    back_to_pending(updated_ticket, request)

                elif updated_ticket.status == 'pending' and previous_status == 'confirmed':
                    with db_transaction.atomic():
                        if ticket.transaction:
                            transaction = ticket.transaction
                            amount_to_deduct = ticket.fare + ticket.commission

                            # Calculate new total amount after deduction
                            new_total_amount = max(transaction.total_amount - amount_to_deduct, 0)

                            # Deduct from total_amount
                            transaction.total_amount = new_total_amount

                            # Adjust paid_amount based on the new total_amount
                        


                            adjust_payments(transaction, request)
                            # Remove the ticket from the transaction
                            # If you simply want to unlink the ticket, you could do:
                            ticket.transaction = None
                            ticket.save()
                            transaction.save()

                            transaction.update_status()

                    
                                

                            

                            



                    
                messages.success(request, 'Ticket booking updated successfully!')
                return redirect('list_tickets')
        else:
            form = BookingForm(instance=ticket)
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while updating the ticket.")
        form = BookingForm(instance=ticket)
    
    context = {
        'form': form,
        'ticket': ticket,
        'customers': Customer.objects.all(),
        'suppliers': Supplier.objects.all(),
        'city': City.objects.all()
    }
    return render(request, 'Dashboard/tickets/update_ticket.html', context)    


def log_action(request, ticket):
    action = 'cancel_ticket' if ticket.status == 'canceled' else 'reactivate_ticket'
    content_type = ContentType.objects.get_for_model(ticket)
    object_id = ticket.pk

    ActivityLog.objects.create(
        user=request.user,
        action=action,
        content_type=content_type,
        object_id=object_id,
        description=f'{action} processed for ticket of {ticket.passenger_name}'
    )






# visa lists to manage visa bookings
@login_required
@permission_required('Agency.view_visa', raise_exception=True)  # Ensure this permission is correctly defined

def list_visa_bookings(request):
    try:
        query = request.GET.get('query', '')
        if query:
            visas = VisaBooking.objects.filter(
                Q(customer__name__icontains=query) | 
                Q(country__icontains=query)
            )
        else:
            visas = VisaBooking.objects.all().order_by('-date_created')

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

        return render(request, 'Dashboard/visas/visa_booking_list.html', {'page_obj': page_obj})
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while fetching the visa bookings.")
        return render(request, 'Dashboard/visas/visa_booking_list.html', {'page_obj': None})



@login_required
@permission_required('Agency.add_city', raise_exception=True)
def city_register(request):
    try:
        if request.method == 'POST':
            form = cityForm(request.POST)
            if form.is_valid():
                new_city = form.save(commit=False)
                new_city.user = request.user
                new_city.save()
                messages.success(request, 'City registered successfully!')

                return redirect('cities')
        else:
            form = cityForm()
        return render(request, 'Dashboard/city/city_regester.html', {'form': form})
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred during city registration.")
        form = cityForm()  # Reinitialize form to clear data
        return render(request, 'Dashboard/city/city_regester.html', {'form': form})


@login_required
@permission_required('Agency.view_city', raise_exception=True)
def city_view(request):
    try:
        query = request.GET.get('query', '')
        cities = City.objects.filter(name__icontains=query) if query else City.objects.all().order_by('-created_at')

        paginator = Paginator(cities, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'Dashboard/city/manage_cities.html', {'page_obj': page_obj, 'query': query})
    except Exception as e:
        log_error(request, e)
        messages.error(request, "Failed to load city list.")
        return render(request, 'Dashboard/city/manage_cities.html', {'page_obj': None})




@login_required
@permission_required('Agency.change_city', raise_exception=True)
def city_update(request, id):
    try:
        city = get_object_or_404(City, id=id)
        if request.method == 'POST':
            form = cityForm(request.POST, instance=city)
            if form.is_valid():
                updated_city = form.save(commit=False)
                updated_city.user = request.user
                updated_city.save()
                messages.success(request, 'City updated successfully!')

                return redirect('cities') 
        else:
            form = SupplierUpdateForm(instance=city)
        context = {'form': form, 'supplier': city}
        return render(request, 'Dashboard/city/city_update.html', context)
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while updating the city.")
        form = cityForm(instance=city)  # Reset form with initial instance

    return render(request, 'Dashboard/city/city_update.html', {'form': form, 'city': city})






# visa booking regesteration 
@login_required
@permission_required('Agency.add_visabooking', raise_exception=True)
def visa_booking_register(request):
    try:
        form = VisaBookingForm(request.POST or None, request.FILES or None)
        customers = Customer.objects.all()
        countries = Country.objects.all()
        
        if request.method == 'POST' and form.is_valid():
            new_visa_booking = form.save(commit=False)
            new_visa_booking.user = request.user
            new_visa_booking.save()

            Expense.objects.create(
                category='Other',
                amount=new_visa_booking.visa_fee,
                description=f'Visa booking fee for visa ID {new_visa_booking.id} {new_visa_booking.name}',
                payment_method='evc_plus',
                date_created=timezone.now(),
                paid_by=request.user
            )
            messages.success(request, 'Visa booking successfully created!')
            return redirect('visa_bookings_list')
    except Exception as e:
        log_error(request, e)

        messages.error(request, f"An error occurred while regestering visa")

    return render(request, 'Dashboard/visas/visa_register.html', {
        'form': form,
        'customers': customers,
        'age_choices': VisaBooking.AGE_CHOICES,
        'countries': countries
    })






# the update function of visa bookings
@login_required
@permission_required('Agency.change_visabooking', raise_exception=True)
def update_visa_booking(request, id):
    try:
        visa = get_object_or_404(VisaBooking, pk=id)
        form = VisaBookingForm(request.POST or None, request.FILES or None, instance=visa)
        
        if request.method == 'POST' and form.is_valid():
            updated_visa = form.save(commit=False)
            updated_visa.user = request.user
            updated_visa.save()

            if updated_visa.status == 'canceled':
                adjust_financial_records_for_visa_cancellation(updated_visa, request)
            elif updated_visa.status == 'pending' and visa.status == 'canceled':
                back_to_pending_visa(updated_visa, request)
            elif updated_visa.status == 'pending' and visa.status == 'confirmed':
                adjust_for_confirmed_to_pending_visa(updated_visa, request)

            messages.success(request, 'Visa booking updated successfully!')
            return redirect('visa_bookings_list')
    except Exception as e:
        log_error(request, e)
        messages.error(request, f"An error occurred while updating visa:")
    return render(request, 'Dashboard/visas/visa_booking_update.html', {
        'form': form,
        'visa': visa,
        'customers': Customer.objects.all(),
        'age_choices': VisaBooking.AGE_CHOICES,
        'countries': Country.objects.all()
    })



def adjust_financial_records_for_visa_cancellation(visa, request):
    try:
        with db_transaction.atomic():
            if visa.transaction:
                transaction = visa.transaction
                amount_to_deduct = visa.visa_fee + visa.commission

                new_total_amount = max(transaction.total_amount - amount_to_deduct, 0)
                transaction.total_amount = new_total_amount


                adjust_payments(transaction)
            
                visa.transaction = None
                visa.save()
                transaction.save()
                transaction.update_status()

            update_expense_record_for_visa(visa,request)
            log_visa_action(visa, request)
            messages.info(request, f"All financial records for {visa.name} have been adjusted due to cancellation.")


    except Exception as e:
        log_error(request, e)

        messages.error(request, f"An error occurred while dealing financial records")



def adjust_for_confirmed_to_pending_visa(visa, request):
    try:

        with db_transaction.atomic():
            if visa.transaction:
                transaction = visa.transaction
                amount_to_deduct = visa.visa_fee + visa.commission

                # Calculate new total amount after deduction
                new_total_amount = max(transaction.total_amount - amount_to_deduct, 0)

                # Deduct from total_amount
                transaction.total_amount = new_total_amount
                
                adjust_payments(transaction)


                # Adjust paid_amount based on the new total_amount

                transaction.save()

                transaction.update_status()

                visa.transaction = None
                visa.save()
            transaction.save()

            transaction.update_status()
    except Exception as e:
        log_error(request, e)

        messages.error(request, f"An error occurred while dealing financial records")




def back_to_pending_visa(visa, request):
    try:
        expense = Expense.objects.get(description=f'Visa booking fee for visa ID {visa.id} {visa.name}')
        expense.amount = visa.visa_fee
        expense.save()
        messages.info(request, f"Financial records for {visa.name} have been adjusted back to pending status.")
    except Expense.DoesNotExist:
        # Optionally handle the absence of an existing record
        pass

    except Exception as e:
        log_error(request, e)

        messages.error(request, f"An error occurred while dealing financial records")

def log_visa_action(visa, request):
    action = 'cancel_visa' if visa.status == 'canceled' else 'reactivate_visa'
    content_type = ContentType.objects.get_for_model(visa)
    object_id = visa.pk

    ActivityLog.objects.create(
        user=request.user,
        action=action,
        content_type=content_type,
        object_id=object_id,
        description=f'{action} processed for visa of {visa.name}'
    )

def update_expense_record_for_visa(visa,request):
    try:
        expense = Expense.objects.get(description=f'Visa booking fee for visa ID {visa.id} {visa.name}')
        expense.amount = 0
        expense.description = f'Visa booking fee for visa ID {visa.id} {visa.name} is assigned 0 due to cancellation'
        expense.save()
    except Expense.DoesNotExist:
        # Handle case where no expense record exists
        pass
    except Exception as e:
        log_error(request, e)

        messages.error(request, f"An error occurred while dealing financial records")




# the start of the invoice creation
@login_required
@permission_required('Agency.add_transaction', raise_exception=True)
def select_customer(request):
    customers = Customer.objects.all()
    try:
        if request.method == 'POST':
            customer_id = request.POST.get('customer')
            booking_type = request.POST.get('transaction_type')
            if booking_type == 'ticket':
                return redirect('customer_ticket_pending_bookings', customer_id=customer_id)
            elif booking_type == 'visa':
                return redirect('customer_pending_visa_bookings', customer_id=customer_id)
            
    except Exception as e:
        log_error(request, e)

        messages.error(request, f"An error occurred while choosing the customer of the booking")

    return render(request, 'Dashboard/invoices/ticket_invoice_register.html', {'customers': customers})








@login_required
@permission_required('Agency.add_transaction', raise_exception=True)
def customer_ticket_pending_bookings(request, customer_id):
    try:
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
                    # context = { 
                    #     'customer_name': customer.name,
                    #     'customer_no': customer.phone,
                    #     'date': transaction.transaction_date.strftime('%d.%m.%Y'),
                    #     'invoice_no': transaction.reference_number,
                    #     'transaction_type': transaction.transaction_type,
                    #     'transaction_no': transaction.id,
                    #     'bookings': selected_bookings,
                    #     'subtotal': total_amount,
                    #     'partial': transaction.paid_amount,
                    #     'total': transaction.total_amount,
                    #     'remaining_amount' : total_amount - transaction.paid_amount,
                    #     'due_date':transaction.transaction_date,
                    #     'status':transaction.status,
                    #     'b':b,
                    #     'path_to_signature': '/path/to/your/signature.png'  # Update with the actual path to the signature
                    # }
                    # return render(request, 'Dashboard/invoices/ticket_invoice_template.html', context)
                    return redirect('view_invoice',invoice_id=transaction.id)
        else:
            booking_form = BookingSelectionForm()
            payment_form = PaymentForm()

    except Exception as e:
        log_error(request, e)

        messages.error(request, f"An error occurred while adding bookings to the invoice")


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
    try:
        query = request.GET.get('query', '')
        if query:
            invoices = Transaction.objects.filter(
                Q(customer__name__icontains=query) | 
                Q(reference_number__icontains=query)
            )
        else:
            invoices = Transaction.objects.all().order_by('-transaction_date')

        # Pagination setup
        paginator = Paginator(invoices, 10)  # Display 10 invoices per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        log_error(request, e)
        messages.error(request, f"An error occurred while listing the invoices")


    return render(request, 'Dashboard/invoices/invoice_list.html', {'page_obj': page_obj})





# the view of all invoices
@login_required
@permission_required('Agency.view_transaction', raise_exception=True)
def view_invoices(request, invoice_id):
    try:
        invoice = get_object_or_404(Transaction, id=invoice_id)
        
        if invoice.transaction_type == 'ticket':
            # Exclude canceled bookings directly in the query using exclude()
            selected_bookings = TicketBooking.objects.filter(transaction=invoice).exclude(status__in=['canceled', 'pending'])
            for booking in selected_bookings:
                booking.total_cost = booking.fare + booking.commission
            subtotal = sum(b.fare + b.commission for b in selected_bookings)
        
        elif invoice.transaction_type == 'visa':
            # Exclude canceled visa bookings directly in the query using exclude()
            selected_bookings = VisaBooking.objects.filter(transaction=invoice).exclude(status__in=['canceled', 'pending'])
            for booking in selected_bookings:
                booking.total_cost = booking.visa_fee + booking.commission
            subtotal = sum(booking.visa_fee + booking.commission for booking in selected_bookings)
        
        remaining_amount = subtotal - invoice.paid_amount
        remaining_amount = max(0, remaining_amount)  # Ensuring remaining amount is never negative
        
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
            'status': invoice.status,
            'path_to_signature': '/path/to/your/signature.png',  # Update with the actual path to the signature
            'logo_url': '/path/to/your/logo.png'  # Update with the actual path to the logo
        }

        if invoice.transaction_type == 'ticket':
            return render(request, 'Dashboard/invoices/ticket_invoice_template.html', context)
        elif invoice.transaction_type == 'visa':
            return render(request, 'Dashboard/invoices/visa_invoice_template.html', context)

    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while fetching the invoice details.")
        return render(request, 'Dashboard/error_page.html', {'error': str(e)})






# the completion of transaction if it is have 
@login_required
@permission_required('Agency.add_transaction', raise_exception=True)
def incomplete_transactions(request):
    try:
        # Fetch transactions with a remaining amount greater than 0
        transactions = Transaction.objects.annotate(
            remaining=ExpressionWrapper(F('total_amount') - F('paid_amount'), output_field=DecimalField())
        ).filter(remaining__gt=0).order_by('-transaction_date')

        # Calculate the total of all remaining amounts
        total_remaining = transactions.aggregate(total=Sum('remaining'))['total']

        # Provide the transactions and the total remaining to the template
        context = {
            'transactions': transactions,
            'total_remaining': total_remaining
        }
        return render(request, 'Dashboard/invoices/ticket_incomplete_transactions.html', context)
    except Exception as e:
        log_error(request, e)  # Log the exception to your logging system
        messages.error(request, "An error occurred while fetching incomplete transactions.")
        return render(request, 'Dashboard/error_page.html', {'error': str(e)})

@login_required
@permission_required('Agency.add_transaction', raise_exception=True)
def complete_payment(request, transaction_id):
    try:
     
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
    except Exception as e:
        log_error(request, e)
        messages.error(request, 'An error occurred while processing the payment.')
        return render(request, 'Dashboard/invoices/ticket_complete_payment.html', {
                    'transaction': transaction,
                    'previous_payments': previous_payments,
                    'payment_form': payment_form,
                    'remaining_amount': transaction.total_amount - transaction.paid_amount,
                })








@login_required
@permission_required('Agency.add_transaction', raise_exception=True)
def customer_pending_visa_bookings(request, customer_id):
    try:
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
                    # context = {
                    #     'customer_name': customer.name,
                    #     'customer_no': customer.phone,
                    #     'date': transaction.transaction_date.strftime('%d.%m.%Y'),
                    #     'invoice_no': transaction.reference_number,
                    #     'transaction_type': transaction.transaction_type,
                    #     'transaction_no': transaction.id,
                    #     'bookings': selected_bookings,
                    #     'subtotal': total_amount,
                    #     'partial': transaction.paid_amount,
                    #     'total': transaction.total_amount,
                    #     'remaining_amount': total_amount - transaction.paid_amount,
                    #     'path_to_signature': '/path/to/your/signature.png'  # Update with the actual path to the signature
                    # }

                    return redirect('view_invoice', invoice_id=transaction.id)
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
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while processing visa bookings.")
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
    try:
        if request.method == 'POST':
            form = EmployeeForm(request.POST, request.FILES)
            if form.is_valid():
                new_employee = form.save()
                new_employee.request_user = request.user 
                new_employee.save()
                messages.success(request, 'Employee registered successfully!')
                return redirect('employee_list')  # Redirect to the list of employees on success
        else:
            form = EmployeeForm()

        return render(request, 'Dashboard/HR/employee_register.html', {'form': form})
    
    except Exception as e:
        # Log the exception here if logging is set up
        log_error(request, e)
        messages.error(request, 'An error occurred during the registration process. Please try again.')
        form = EmployeeForm()  
        return render(request, 'Dashboard/HR/employee_register.html', {'form': form})





# list of the employees to manage
@login_required
@permission_required('Agency.view_employee', raise_exception=True)
def employee_list(request):
    try:
        search_query = request.GET.get('search', '')
        if search_query:
            employees = Employee.objects.filter(
                Q(name__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(phone__icontains=search_query)
            )
        else:
            employees = Employee.objects.all().order_by('-created_at')

        # Set up pagination
        paginator = Paginator(employees, 10)  # Shows 10 employees per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'page_obj': page_obj
        }
        return render(request, 'Dashboard/HR/manage_employees.html', context)

    except Exception as e:
        # Log the exception here
        log_error(request, e)

        messages.error(request, 'An error occurred while fetching the employee list. Please try again.')
        return render(request, 'Dashboard/HR/manage_employees.html', {'page_obj': None})
   






@login_required
@permission_required('Agency.change_employee', raise_exception=True)
def employee_update(request, employee_id=None):
    try:
        if employee_id:
            employee = get_object_or_404(Employee, pk=employee_id)
            form = EmployeeForm(request.POST or None, request.FILES or None, instance=employee)
        else:
            form = EmployeeForm(request.POST or None, request.FILES or None)

        if request.method == 'POST':
            if form.is_valid():
                updated_employee = form.save()
                updated_employee.request_user = request.user 
                updated_employee.save()
                messages.success(request, 'Expense record regestered successfully!')
                return redirect('employee_list')  # Redirect to the employee list view

        return render(request, 'Dashboard/HR/employee_update.html', {'form': form, 'employee': employee if employee_id else None})
    except Exception as e:
        log_error(request, e)
        messages.error(request, 'An error occurred while processing your request.')
        # Return to the same page with the form and possibly the employee instance if it was loaded
        return render(request, 'Dashboard/HR/employee_update.html', {'form': form, 'employee': employee})






# the list of expense
@login_required
@permission_required('Agency.view_expense', raise_exception=True)
def expense_list(request):
    try:
        query = request.GET.get('query', '')
        if query:
            expenses = Expense.objects.filter(
                Q(category__icontains=query) |
                Q(description__icontains=query) |
                Q(amount__icontains=query)  # Note: filtering by amount might need exact matches unless amount is a CharField
            )
        else:
            expenses = Expense.objects.all().order_by('-date_created')

        # Set up pagination
        paginator = Paginator(expenses, 10)  # Shows 10 expenses per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'Dashboard/expenses/expenses.html', {'page_obj': page_obj})

    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while fetching the expense list.")
        return render(request, 'Dashboard/expenses/expenses.html', {'page_obj': None})



# expense record regesteration
@login_required
@permission_required('Agency.add_expense', raise_exception=True)
def record_expense(request):
    try:
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

    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while recording the expense. Please try again.")
        # Reset form and context to avoid displaying potentially incorrect or sensitive data
        form = ExpenseForm()
        context = {
            'form': form,
            'payment_methods': Transaction.PAYMENT_METHOD_CHOICES,
            'Expense_category': Expense.EXPENSE_CATEGORY_CHOICES,
        }
        return render(request, 'Dashboard/expenses/expense_payments.html', context)






# the update of the expense
@login_required
@permission_required('Agency.change_expense', raise_exception=True)
def expense_update(request, expense_id):
    try:
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
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while updating the expense. Please try again.")
        return render(request, 'Dashboard/expenses/expense_payments_update.html', {'form': form})






@login_required
@permission_required('Agency.add_asset', raise_exception=True)
def register_asset(request):
    try:
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

    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while registering the asset. Please try again.")
        form = AssetForm()  # Reinitialize the form to clear previous data
        return render(request, 'Dashboard/purchase_assets/asset_register.html', {'form': form})






@login_required
@permission_required('Agency.view_asset', raise_exception=True)
def list_assets(request):
    try:
        query = request.GET.get('query', '')
        if query:
            assets = Asset.objects.filter(
                Q(asset_name__icontains=query) |
                Q(description__icontains=query) |
                Q(user__username__icontains=query)
            )
        else:
            assets = Asset.objects.all().order_by('-purchase_date')

        # Set up pagination
        paginator = Paginator(assets, 10)  # Show 10 assets per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
       

        return render(request, 'Dashboard/purchase_assets/manage_assets.html', {'page_obj': page_obj, 'query': query})

    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while fetching the assets. Please try again.")
        return render(request, 'Dashboard/purchase_assets/manage_assets.html', {'page_obj': None})




@login_required
@permission_required('Agency.change_asset', raise_exception=True)
def update_asset(request, id):
    try:
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
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while updating the asset. Please try again.")
        return render(request, 'Dashboard/purchase_assets/update_asset.html', {'form': form})





def get_current_year_range():
    today = timezone.now()
    return (timezone.make_aware(datetime(today.year, 1, 1)), 
            timezone.make_aware(datetime(today.year + 1, 1, 1)))



# the dashboard home pahe
@login_required
def index(request):
    try:
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

        this_month_revenue = total_current_month_fare + total_current_month_commission

        last_month_revenue = total_last_month_commission + total_last_month_fare


        revenue_change = this_month_revenue - last_month_revenue

        percentage_change = (revenue_change / last_month_revenues * 100) if last_month_revenues else 0
        percentage_change = min(percentage_change, 100)

        if total_last_month_commission > Decimal(0):
            commision_change = total_current_month_commission - total_last_month_commission
            commision_percentage_change = (commision_change / total_last_month_commission * 100)
            commision_percentage_change = min(percentage_change, 100)
        else:
        # Handle the case where there is no previous commission to compare against
            commision_change = total_current_month_commission - total_last_month_commission
            # Set percentage change to 0 or another appropriate value
            commision_percentage_change = Decimal(0) 

        

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

        # print(months)
        # print(expenses_values)
        # print(f"Current Month Revenues: {current_month_revenues}")
        # print(f"Last Month Revenues: {last_month_revenues}")
        # print(f"Current Month Expenses: {current_month_expenses}")
        # print(f"Last Month Expenses: {last_month_expenses}")


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
            'commision_percentage_change':commision_percentage_change,


        }

        return render(request, 'Dashboard/index.html', context)
    
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while generating the dashboard. Please contact support.")
        return render(request, 'Dashboard/index.html',status=500)


# def homepage(request):
#     return render(request,'Dashboard/index1.html')







@login_required
@permission_required('Users.role_report', raise_exception=True)
def booking_report(request): 
    try:
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
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

                ticket_bookings = TicketBooking.objects.filter(travel_date__range=(start_date, end_date))
                for booking in ticket_bookings:
                    booking.total_cost = booking.fare + booking.commission
                visa_bookings = VisaBooking.objects.filter(departure_date__range=(start_date, end_date))
            except ValueError:
                messages.error(request, "Invalid date format. Please use YYYY-MM-DD format.")
                return render(request,'Dashboard/Reports/Booking_reports.html')


        else:
            ticket_bookings = TicketBooking.objects.all()
            visa_bookings = VisaBooking.objects.all()

        # Calculating totals
        context['ticket_bookings'] = ticket_bookings
        context['visa_bookings'] = visa_bookings
        context['total_fares'] = sum(b.fare for b in ticket_bookings) + sum(b.visa_fee for b in visa_bookings)
        context['total_commissions'] = sum(b.commission for b in ticket_bookings) + sum(b.commission for b in visa_bookings)
    
    
        return render(request,'Dashboard/Reports/Booking_reports.html',context)
    except Exception as e:
        # Log the error
        log_error(request, e)
        messages.error(request, "An error occurred while generating the booking report. Please try again.")
        return render(request, 'Dashboard/Reports/Booking_reports.html', {'error': 'An error occurred'})






@login_required
@permission_required('Users.role_report', raise_exception=True)
def expense_report(request):
    try:
        # Extract dates from GET parameters
        start_date = request.GET.get('startDate')
        end_date = request.GET.get('endDate')

        # Convert string dates to date objects
        start_date = parse_date(start_date) if start_date else None
        end_date = parse_date(end_date) if end_date else None

        # Initialize the query to fetch all expenses or within date range if specified
        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                expenses = Expense.objects.filter(date_created__date__range=(start_date, end_date))
            except ValueError:
                messages.error(request, "Invalid date format. Please use YYYY-MM-DD format.")
                return render(request, 'Dashboard/Reports/expense_report.html', {
            'expenses': [],
            'start_date': start_date,
            'end_date': end_date
        })

            
        else:
            expenses = Expense.objects.all()

        return render(request, 'Dashboard/Reports/expense_report.html', {
            'expenses': expenses,
            'start_date': start_date,
            'end_date': end_date
        })
    except Exception as e:
        # Log the error
        log_error(request, e)
        messages.error(request, "An error occurred while generating the booking report. Please try again.")
        return render(request, 'Dashboard/Reports/Booking_reports.html', {'error': 'An error occurred'})






# the customer report
@login_required
@permission_required('Users.role_report', raise_exception=True)
def customer_report(request):
    try:
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
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                customers = customers.annotate(
                    total_paid=Sum('transaction__payment__amount',
                                filter=Q(transaction__transaction_date__range=[start_date, end_date])
                                )
                ).order_by('-total_paid') 
            except ValueError:
                messages.error(request, "Invalid date format. Please use YYYY-MM-DD format.")
                return render(request, 'Dashboard/Reports/customer_report.html', {
                    'customers': [],
                    'start_date': start_date,
                    'end_date': end_date,
                    'error': 'Invalid date format provided'
                })
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
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while generating the customer report. Please try again.")
        return render(request, 'Dashboard/Reports/customer_report.html', {
            'customers': customers,
            'start_date': start_date,
            'end_date': end_date,
            'error': 'An error occurred'
        })





# the supplier report
@login_required
@permission_required('Users.role_report', raise_exception=True)
def supplier_report(request):
    try:
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
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while generating the supplier report. Please try again.")
        return render(request, 'Dashboard/Reports/supplier_report.html', {
            'suppliers': suppliers,
            'start_date': start_date,
            'end_date': end_date,
            'error': 'An error occurred'
        })




@login_required
@permission_required('Users.role_report', raise_exception=True)
def departure_report(request):
    try:
        search_query = request.GET.get('search', '')
        departure_date = request.GET.get('departure_date', '')  # Updated to match form field name

        departures = TicketBooking.objects.all().order_by('-travel_date')

        if search_query:
            departures = departures.filter(destination__name__icontains=search_query)

        if departure_date:
            # Convert the string date to a datetime object
            try:
                formatted_date = timezone.datetime.strptime(departure_date, '%Y-%m-%d').date()
                departures = departures.filter(travel_date=formatted_date)
            except ValueError:
                # Handle invalid date format
                departures = departures.none()

        context = {
            'departures': departures,
            'search_query': search_query,
            'departure_date': departure_date,
            'today': timezone.now(),
        }
        return render(request, 'Dashboard/Reports/departure_report.html', context)
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An unexpected error occurred while generating the departure report. Please try again.")
        return render(request, 'Dashboard/Reports/departure_report.html', {
            'departures': departures,
            'search_query': search_query,
            'departure_date': departure_date,
            'today': timezone.now(),
            'error': 'An unexpected error occurred'
        })





@login_required
@permission_required('Users.role_report', raise_exception=True)
def sales_report(request):
    transactions = []  # Initialize transactions to an empty list to ensure it's always defined
    start_date = request.GET.get('startDate', timezone.now().date().strftime('%Y-%m-%d'))
    end_date = request.GET.get('endDate', timezone.now().date().strftime('%Y-%m-%d'))
    
    try:
        # Convert string dates to date objects
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        tickets = TicketBooking.objects.filter(
            booking_date__range=[start_date, end_date]
        ).annotate(
            transaction_type=Value('Ticket', output_field=CharField()),
            date=F('booking_date'),
            amount=ExpressionWrapper(F('fare') + F('commission'), output_field=DecimalField())
        ).values(
            'id', 'date', 'customer__name', 'transaction_type', 'amount', 'user__username'
        )

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
        transactions = list(chain(tickets, visas))
        transactions.sort(key=lambda x: x['date'])

    except ValueError:
        messages.error(request, "Invalid date format. Please use YYYY-MM-DD format.")
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while generating the sales report. Please try again.")

    return render(request, 'Dashboard/Reports/sales_report.html', {
        'transactions': transactions,
        'start_date': start_date,
        'end_date': end_date
    })
@login_required
@permission_required('Users.role_report', raise_exception=True)
def assets_report(request):
    try:
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
    # except ValueError as e:
    #     # Handle specific errors such as invalid date formats
    #     messages.error(request, "Invalid date format. Please use YYYY-MM-DD format.")
    #     logging.error(f"Date parsing error in assets_report: {str(e)} - User: {request.user.Username if request.user.is_authenticated else 'Anonymous'}")
    except Exception as e:
        # General error handling for any other unanticipated errors
        log_error(request, e)
        messages.error(request, "An unexpected error occurred while generating the assets report. Please try again.")
        return render(request, 'Dashboard/Reports/assets_report.html', {
            'assets': [],
            'start_date': start_date,
            'end_date': end_date
        })











@login_required
@permission_required('Users.role_report', raise_exception=True)
def income_statement(request):

    try:
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
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while generating the income statement. Please try again.")
        context = {'start_date': start_date,
                    'end_date': end_date,
                    'total_ticket_sales': total_ticket_sales,
                    'total_visa_fees': total_visa_fees,
                    'total_revenues': total_revenues,
                    'total_expenses': total_expenses,
                    'net_income': net_income}
        return render(request, 'Dashboard/Reports/income_statement.html', context)






@login_required
@permission_required('Agency.add_transaction', raise_exception=True)
def edit_transaction(request, transaction_id):
    try:
        transaction = get_object_or_404(Transaction, id=transaction_id)
        if transaction.transaction_type == 'ticket':
            pending_bookings = TicketBooking.objects.filter(customer=transaction.customer, status='pending')
            transaction_bookings = TicketBooking.objects.filter(transaction=transaction)
        
        elif transaction.transaction_type == 'visa':
            pending_bookings = VisaBooking.objects.filter(customer=transaction.customer, status='pending')
            transaction_bookings = VisaBooking.objects.filter(transaction=transaction)
            
        previous_payments = Payment.objects.filter(transaction=transaction)

        no_pending_bookings = not pending_bookings.exists()
        payment_form = PaymentForm(request.POST or None)        

        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'update_transaction' and payment_form.is_valid():
                payment_method = payment_form.cleaned_data['payment_method']
                amount = payment_form.cleaned_data['paid_amount']
                new_total_paid = transaction.paid_amount + amount
                if new_total_paid > transaction.total_amount:
                    messages.error(request, "Paid amount can not be grater than the remaining amount")
                    return redirect('edit_transaction', transaction_id=transaction_id)
                with db_transaction.atomic():
                    Payment.objects.create(
                        transaction=transaction,
                        amount=amount,
                        payment_method=payment_method,
                        user=request.user
                    )
                    transaction.paid_amount += amount
                    transaction.save()
                    update_transaction_total(transaction)
                    messages.success(request, "Transaction updated successfully.")

                    return redirect('view_invoice', invoice_id=transaction.id)
            elif action == 'add_bookings':
                selected_booking_ids = request.POST.getlist('bookings')
                model = TicketBooking if transaction.transaction_type == 'ticket' else VisaBooking
            with db_transaction.atomic():
                for booking_id in selected_booking_ids:
                    booking = get_object_or_404(model, id=booking_id)
                    if booking.status != 'canceled':
                        booking.transaction = transaction
                        booking.status = 'confirmed'
                        booking.save()
                update_transaction_total(transaction)
                messages.success(request, "Bookings added to the transaction.")
                return redirect('edit_transaction', transaction_id=transaction_id)

        context = {
            'transaction': transaction,
            'pending_bookings': pending_bookings,
            'transaction_bookings': transaction_bookings,
            'previous_payments': previous_payments,
            'no_pending_bookings': no_pending_bookings,
            'payment_form': payment_form,
            'total_amount': transaction.total_amount,
            'paid_amount': transaction.paid_amount,
            'remaining': transaction.total_amount - transaction.paid_amount,
        }
        return render(request, 'Dashboard/invoices/invoice_update.html', context)
    except Exception as e:
        log_error(request, e)
        messages.error(request, "An error occurred while updating the transaction. Please try again.")
        return redirect('edit_transaction', transaction_id=transaction_id)

def update_transaction_total(transaction):
    bookings = TicketBooking.objects.filter(transaction=transaction, status='confirmed') if transaction.transaction_type == 'ticket' else VisaBooking.objects.filter(transaction=transaction, status='confirmed')
    total_amount = sum((booking.fare + booking.commission) if transaction.transaction_type == 'ticket' else (booking.visa_fee + booking.commission) for booking in bookings)
    transaction.total_amount = total_amount
    transaction.save()
    transaction.update_status()