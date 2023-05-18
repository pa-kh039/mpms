from django.shortcuts import render, redirect
# from django.contrib.auth.models import User,auth
from django.contrib.auth.models import auth
from .models import * 
from django.core.mail import send_mail
# from django.conf import settings
from django.contrib import messages

import datetime
import pytz
import razorpay
import uuid
from mlp.settings import RAZORPAY_API_KEY,RAZORPAY_API_SECRET_KEY,EMAIL_HOST_USER

# Create your views here.
def index(request):
    return render(request,'index.html')

def register(request):
    if request.method=="POST":
        # username=request.POST['username']
        email=request.POST['email']
        phone=request.POST['phone']
        password=request.POST['password']
        password2=request.POST['password2']

        if password==password2:
            if User.objects.filter(email=email).exists():
                messages.info(request,'Email already used')
                return redirect('register')
            
            else:
                auth_token=str(uuid.uuid4())
                user=User.objects.create_user(email=email,password=password,phone=phone,auth_token=auth_token)
                user.save()
                send_mail_after_registration(email,auth_token)
                return redirect('/verifyemail')
        else:
            messages.info(request,"Both passwords are different")
            return redirect('register')
            
    return render(request,'register.html')

def verifyemail(request):
    return render(request,'emailsent.html')

def verify(request,auth_token):
    user_obj=User.objects.filter(auth_token=auth_token).first()
    if user_obj:
        if not user_obj.is_verified:
            user_obj.is_verified=True 
            user_obj.save()
        messages.success(request,'email verified!')
        return redirect('/login')
    else:
        messages.error('Could not verify ..')
        return redirect('/register')


def login(request):
    if request.method=="POST":
        email=request.POST['email']
        password=request.POST['password']

        user_obj=User.objects.filter(email=email).first()
        if not user_obj.is_verified:
            messages.error(request,"Verify email first")
            return redirect('/login')

        user=auth.authenticate(email=email,password=password) 
        #checking if the user with the given email and password exists in the databse or not
        
        if user is not None:
            auth.login(request,user)  #yaha user ko login karwa diya
            messages.info(request,'Logged In')
            return redirect('/entry')
        else:
            messages.info(request,'Invalid credentials')
            return redirect('login')
    return render(request, 'login.html')

def logout(request):
    auth.logout(request)
    return redirect('/')

def settings(request):
    if request.method=='POST':
        totalfloors=request.POST['totalfloors']
        fpi=request.POST['fpi']
        threshold=request.POST['threshold']
        current_user_entry=User.objects.get(email=request.user)
        current_user_entry.totalfloors=totalfloors
        current_user_entry.fpi=fpi
        current_user_entry.threshold=threshold
        current_user_entry.save()
        messages.info(request,"Settings updated")
    else:
        current_user_entry=User.objects.get(email=request.user)
        totalfloors=current_user_entry.totalfloors
        fpi=current_user_entry.fpi
        threshold=current_user_entry.threshold
    return render(request,'settings.html',{"fpi":fpi,"threshold":threshold,"totalfloors":totalfloors})

def entry(request):
    if request.method=='POST':
        car_number=(request.POST['car_number']).lower()
        current_time=datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        user=str(request.user)
        new_entry= ParkingEntry.objects.create(user=user,entrytimestamp=current_time,car_number=car_number)
        new_entry.save()
        messages.info(request,'Entry done')
    return render(request,'entry.html')

def exit(request):
    if request.method=='POST':
        car_number=request.POST['car_number']
        last_entry=ParkingEntry.objects.get(user=str(request.user),car_number=car_number)
        time_difference=(datetime.datetime.now(pytz.timezone('Asia/Kolkata'))-last_entry.entrytimestamp).seconds
        # time_difference=type(last_entry.entrytimestamp)
        settings=User.objects.get(email=request.user)
        fpi=settings.fpi
        calculated_fare= 1 + (time_difference//180)*fpi
        request.session['amount']=calculated_fare
        # messages.info(request,"timed:{} fare:{} email:{}".format(time_difference,calculated_fare,str(request.user)))
        # return render(request,'pay.html',{"amount":calculated_fare})
        last_entry.delete()  #assuming this entry is not needed anymore and payment will surely be completed 
        return redirect('pay') 
    return render(request,'exit.html')

client = razorpay.Client(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET_KEY))
def pay(request):
    #this is in paise
    # DATA = {"amount": max(0,100*amount),"currency": "INR","receipt": "receipt#1","notes": {"Receiver": "MPMS","Message": "Thanks!"},"payment_capture":1}
    DATA = {"amount": max(0,100*request.session['amount']),"currency": "INR","receipt": "receipt#1","notes": {"Receiver": "MPMS","Message": "Thanks!"},"payment_capture":1}
    try:
        payment_order=client.order.create(data=DATA)
    except:
        messages.error(request,'Encountered error in creating order with the given details... you may try again')
        return redirect('exit')
    payment_order_id=payment_order['id']
    context={'amount':max(0,request.session['amount']), 'api_key':RAZORPAY_API_KEY,'order_id':payment_order_id} 
    return render(request,'pay.html',context)

def floor(request):
    if request.method=='POST':
        floor_number=request.POST['floor_number']
        car_number=request.POST['car_number']
        current_user=str(request.user)
        try:
            current_entry=ParkingEntry.objects.get(user=current_user,car_number=car_number)
        except:
            messages.info(request,'Encountered error... probably this car does not exist in database')
            return render(request,'floor.html')
        current_entry.floor_last_seen=floor_number
        current_entry.save()
        messages.info(request,'Floor and car noted')
    return render(request,'floor.html')

def send_mail_after_registration(email,token):
    subject="Your account needs to be verified"
    message= "Visit this link for verification: http://127.0.0.1:8000/verify/{}".format(token)
    email_from=EMAIL_HOST_USER
    recipient_list=[email]
    send_mail(subject,message,email_from,recipient_list)
    return True