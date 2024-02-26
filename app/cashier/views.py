from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth import logout as auth_logout
from decimal import Decimal, InvalidOperation

import matplotlib.pyplot as plt
import io

from .models import Gun, Order, Payment
from .forms import CreateGunForm, UpdateGunForm, OrderForm

def main(request):
     return render(request, 'main.html')

def login(request):
    page = 'login'

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            auth_login(request, user) 
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')

    else:
        form = AuthenticationForm()

    context = {'page': page, 'form': form}
    return render(request, 'auth/login.html', context)


def register(request):
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request) 
            return redirect('home')
        else:
            messages.error(request, 'An error occured during registration')
    return render(request, 'auth/register.html', {'form': form})

def logout(request):
    auth_logout(request)
    return redirect(reverse('main'))

def home(request):
    return render(request, 'home.html')

# STAFF AND NON-STAFF
def is_staff(user):
    return user.is_authenticated and user.is_staff

def is_not_staff(user):
    return user.is_authenticated and not user.is_staff

# - List
@login_required(login_url='login')
def list(request):
    guns = Gun.objects.all()

    # Handle search query
    search_query = request.GET.get('search')
    if search_query:
        guns = guns.filter(name__icontains=search_query)

    context = {'records': guns, 'search_query': search_query}
    return render(request, 'admin/list.html', context)


# - Create a record 
@login_required(login_url='login')
@user_passes_test(is_staff, login_url='login')
def create_record(request):
    form = CreateGunForm()
    if request.method == "POST":
        form = CreateGunForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Your record was created!")
            return redirect('login')
    context = {'form': form}
    return render(request, 'admin/create-gun.html', context=context)


# - Update a record 
@login_required(login_url='login')
@user_passes_test(is_staff, login_url='login')
def update_record(request, pk):
    record = Gun.objects.get(id=pk)
    form = UpdateGunForm(instance=record)
    if request.method == 'POST':
        form = UpdateGunForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, "Your record was updated!")
            return redirect('home')
    context = {'form':form}
    return render(request, 'admin/update-gun.html', context=context)


# - Read / View a singular record
@login_required(login_url='login')
def singular_record(request, pk):
    gun = Gun.objects.get(id=pk)
    context = {'gun': gun}
    return render(request, 'admin/view-record.html', context=context)



# - Delete a record
@login_required(login_url='login')
@user_passes_test(is_staff, login_url='login')
def delete_record(request, pk):
    record = Gun.objects.get(id=pk)
    record.delete()
    messages.success(request, "Your record was deleted!")
    return redirect('home')



# - laporan
@login_required(login_url='login')
@user_passes_test(is_staff, login_url='login')
def laporan_transaksi(request):
    total_transactions = Order.objects.count()

    # Calculate total revenue
    total_revenue = Payment.objects.aggregate(Sum('amount'))['amount__sum']

   
    sellers = Order.objects.values('gun__name').annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity').first()


    # Get best-selling products with total quantity and total revenue
    best_sellers = Order.objects.values('gun__name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(ExpressionWrapper(F('quantity') * F('gun__price'), output_field=DecimalField()))
    ).order_by('-total_quantity')[:5]

    context = {
        'total_transactions': total_transactions,
        'total_revenue': total_revenue,
        'best_sellers': best_sellers,
        'sellers': sellers
    }
    return render(request, "admin/laporan_penjualan.html", context)

# -grafik
@login_required(login_url='login')
@user_passes_test(is_staff, login_url='login')
def tampilGrafik(request):
    import pandas as pd

    orders = Order.objects.all()
    data = []
    for order in orders:
        data.append({"gun": order.gun.name, "total_purchase": order.quantity})
    
    df = pd.DataFrame(data)
    df_group = df.groupby("gun").sum().reset_index()
    
    df_group.plot(kind='bar', x='gun', y='total_purchase')
    plt.xlabel("Gun")
    plt.ylabel("Total Items Sold")
    plt.title("Total Number of Items Sold by Gun")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    response = HttpResponse(buf.read(), content_type='image/png')
    plt.close()
    return response


#USER

#order
@login_required(login_url='login')
@user_passes_test(is_not_staff, login_url='login')
def create_order(request):
    if request.method == "POST":
        gun_id = request.POST["gun"]
        quantity = request.POST["quantity"]
        gun = Gun.objects.get(pk=gun_id)
        order = Order.objects.create(
            user=request.user, 
            gun=gun, 
            quantity=quantity
        )
        return redirect("order_detail", pk=order.pk)
    else:
        gun_list = Gun.objects.all()
        return render(request, "user/order.html", {"gun_list": gun_list})
    

@login_required(login_url='login')
@user_passes_test(is_not_staff, login_url='login')
def order_detail(request, pk):
    order = Order.objects.get(pk=pk)
   
    if order.total_price != 0:
        order.discount_percentage = ((order.total_price - order.discounted_total_price) / order.total_price) * 100
    else:
        order.discount_percentage = 0  

    return render(request, "user/order_detail.html", {"order": order})


@login_required(login_url='login')
@user_passes_test(is_not_staff, login_url='login')
def make_payment(request, pk):
    order = Order.objects.get(pk=pk)

    order.discounted_total_price = order.discounted_total_price

   
    if order.total_price != 0:
        order.discount_percentage = ((order.total_price - order.discounted_total_price) / order.total_price) * 100
    else:
        order.discount_percentage = 0  
    
    if request.method == "POST":
        try:
            amount = Decimal(request.POST["amount"])
            if amount < 0:
                raise InvalidOperation("Amount cannot be negative.")
        except InvalidOperation:
            return HttpResponse("Invalid amount. Please enter a valid non-negative decimal.")
        
        is_payment_less = order.is_payment_less()
        
        if not is_payment_less:
            payment = Payment.objects.create(order=order, amount=amount)
            if order.process_purchase():
              
                return redirect('payment_receipt', pk=payment.pk)
            else:
                return HttpResponse("Insufficient stock.")
        else:
            return HttpResponse("Pembayaran kurang dari total harga")
    else:
        
        context = {
            "order": order,
            "discounted_total_price": order.discounted_total_price,
            "discount_percentage": order.discount_percentage,
        }
        return render(request, "user/make-payment.html", context)




@login_required(login_url='login')
@user_passes_test(is_not_staff, login_url='login')
def payment_receipt(request, pk):
    payment = Payment.objects.get(pk=pk)
    order = Order.objects.get(pk=payment.order.pk)
    is_payment_less = order.is_payment_less()
    context = {"payment": payment, "order": order, "is_payment_less": is_payment_less}
    return render(request, "user/payment_receipt.html", context)
