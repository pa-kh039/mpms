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

# for main page
def index(request):
    return render(request,'index.html')

# for registration page
def register(request):
    if request.method=="POST":
        username=request.POST['username']
        email=request.POST['email']
        phone=request.POST['phone']
        password=request.POST['password']
        password2=request.POST['password2']

        if password==password2:
            if User.objects.filter(email=email).exists():
                messages.info(request,'Email already used')
                return redirect('register')
            if User.objects.filter(username=username).exists():
                messages.info(request,'Username already used')
                return redirect('register')
            
            else:
                auth_token=str(uuid.uuid4())
                user=User.objects.create_user(username=username,email=email,password=password,phone=phone,auth_token=auth_token)
                user.save()
                send_mail_after_registration(username,email,auth_token)
                return redirect('/verifyemail')
        else:
            messages.info(request,"Both passwords are different")
            return redirect('register')
            
    return render(request,'register.html')

def verifyemail(request):
    return render(request,'emailsent.html')

def verify(request,auth_token):
    # user_obj=User.objects.filter(auth_token=auth_token).first()
    user_obj=User.objects.get(auth_token=auth_token)
    if user_obj:
        if not user_obj.is_verified:
            user_obj.is_verified=True 
            user_obj.save()
        messages.success(request,'email verified!')
        return redirect('/login')
    else:
        messages.error('Could not verify ..')
        return redirect('/register')

# for login page
def login(request):
    if request.method=="POST":
        username=request.POST['username']
        password=request.POST['password']

        user=auth.authenticate(username=username,password=password) 
        #checking if the user with the given email and password exists in the databse or not
        
        if user is not None:
            # user_obj=User.objects.filter(email=email).first()
            if not user.is_verified:
                messages.error(request,"Verify email first")
                return redirect('/login')


            auth.login(request,user)  #yaha user ko login karwa diya
            messages.info(request,'Logged In')
            return redirect('/settings')
        else:
            messages.info(request,'Invalid credentials')
            return redirect('login')
    return render(request, 'login.html')

def logout(request):
    auth.logout(request)
    return redirect('/')

# for settings page
def settings(request):
    if request.method=='POST':
        totalfloors=request.POST['totalfloors']
        fpi=request.POST['fpi']
        threshold=request.POST['threshold']
        floorcapacity=request.POST['floorcapacity']
        # updating user settings
        # current_user_entry=User.objects.get(email=request.user)
        current_user_entry=User.objects.get(username=request.user)
        current_user_entry.totalfloors=totalfloors
        current_user_entry.fpi=fpi
        current_user_entry.threshold=threshold
        current_user_entry.floorcapacity=floorcapacity
        current_user_entry.save()
        # creating entries for floors of this user
        old_floors=Floors.objects.filter(username=request.user)
        if old_floors:
            for floor in old_floors:
                floor.delete()
        for floor_number in range(1,int(totalfloors)+1):
            floor=Floors.objects.create(username=request.user,floor_number=floor_number,cars_parked=0)
            floor.save()
        messages.info(request,"Settings updated")
    else:
        # current_user_entry=User.objects.get(email=request.user)
        current_user_entry=User.objects.get(username=request.user)
        totalfloors=current_user_entry.totalfloors
        fpi=current_user_entry.fpi
        threshold=current_user_entry.threshold
        floorcapacity=current_user_entry.floorcapacity
    return render(request,'settings.html',{"fpi":fpi,"threshold":threshold,"totalfloors":totalfloors,"floorcapacity":floorcapacity})

def assign_floor(user):
    # user_obj=User.objects.get(email=user)
    user_obj=User.objects.get(username=user)
    floors=Floors.objects.filter(username=user).order_by('floor_number')
    for floor in floors:
        if floor.cars_parked <= (user_obj.floorcapacity*user_obj.threshold)//100:
            floor.cars_parked+=1
            floor.save()
            return floor.floor_number
    return -1

# for entry page
def entry(request):
    if request.method=='POST':
        car_number=(request.POST['car_number']).lower()
        current_time=datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        username=request.user
        floorassigned=assign_floor(request.user)
        if floorassigned==-1:
            messages.error(request,"No space available at any floor.. You may try after some time..")
            return redirect('/entry')
        new_entry= ParkingEntry.objects.create(username=username,entrytimestamp=current_time,car_number=car_number,floor_last_seen=0,floorassigned=floorassigned)
        new_entry.save()
        messages.info(request,'Entry done. Please proceed to \nFLOOR NUMBER {}. \nEntering a different floor will attract fine.'.format(floorassigned))
    return render(request,'entry.html')

def decrement_car_count(user,floor_number):
    floor=Floors.objects.get(username=user,floor_number=floor_number)
    floor.cars_parked-=1
    floor.save()

# for exit page
def exit(request):
    if request.method=='POST':
        car_number=request.POST['car_number']
        try:
            last_entry=ParkingEntry.objects.get(username=request.user,car_number=car_number)
        except:
            messages.error(request,"Encountered error. Maybe car was not found in database..")
            return redirect('exit')
        time_difference=(datetime.datetime.now(pytz.timezone('Asia/Kolkata'))-last_entry.entrytimestamp).seconds
        # time_difference=type(last_entry.entrytimestamp)
        settings=User.objects.get(username=request.user)
        fpi=settings.fpi
        if fpi==None:
            messages.error(request,"Settings incomplete..")
            return redirect('exit')
        fine=0
        if last_entry.floor_last_seen!=last_entry.floorassigned:
            fine+=30
        calculated_fare= 1 + (time_difference//180)*fpi + fine
        # request.session['amount']=calculated_fare
        decrement_car_count(request.user,last_entry.floorassigned)
        last_entry.delete()  #assuming this entry is not needed anymore and payment will surely be completed
        if fine>0:
            messages.info(request,"A fine of {} has been applied".format(fine)) 
        return redirect('pay/{}'.format(calculated_fare)) 
    return render(request,'exit.html')

client = razorpay.Client(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET_KEY))
def pay(request,amount):
    amount=float(amount)
    #this is in paise
    DATA = {"amount": max(0,100*amount),"currency": "INR","receipt": "receipt#1","notes": {"Receiver": "MPMS","Message": "Thanks!"},"payment_capture":1}
    # DATA = {"amount": max(0,100*request.session['amount']),"currency": "INR","receipt": "receipt#1","notes": {"Receiver": "MPMS","Message": "Thanks!"},"payment_capture":1}
    try:
        payment_order=client.order.create(data=DATA)
    except:
        messages.error(request,'Encountered error in creating order with the given details... you may try again')
        return redirect('exit')
    payment_order_id=payment_order['id']
    context={'amount':max(0,amount), 'api_key':RAZORPAY_API_KEY,'order_id':payment_order_id} 
    # context={'amount':max(0,request.session['amount']), 'api_key':RAZORPAY_API_KEY,'order_id':payment_order_id} 
    return render(request,'pay.html',context)

# for floor page
def floor(request):
    if request.method=='POST':
        floor_number=int(request.POST['floor_number'])  #have to cast string to int 
        car_number=request.POST['car_number']
        current_user=request.user
        try:
            current_entry=ParkingEntry.objects.get(username=current_user,car_number=car_number)
        except:
            messages.info(request,'Encountered error... probably this car does not exist in database')
            return render(request,'floor.html')
        if floor_number==current_entry.floor_last_seen:
            messages.info(request,'Car has been seen on this floor already')
            return render(request,'floor.html')
        current_entry.floor_last_seen=floor_number
        current_entry.save()
        messages.info(request,'Floor and car noted')
    return render(request,'floor.html')

def send_mail_after_registration(username,email,token):
    subject="Your account needs to be verified"
    message= "Hello {}! Thanks for registering! Just 1 more step !    Visit this link for verification: http://127.0.0.1:8000/verify/{}".format(username,token)
    email_from=EMAIL_HOST_USER
    recipient_list=[email]
    send_mail(subject,message,email_from,recipient_list)
    return True