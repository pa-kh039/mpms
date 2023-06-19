from django.shortcuts import render, redirect
# from django.contrib.auth.models import User,auth
from django.contrib.auth.models import auth
from .models import * 
from django.core.mail import send_mail
# from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required

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
@login_required(login_url="/login")
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
        dynamicpricing=current_user_entry.dynamicpricing
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
        dynamicpricing=current_user_entry.dynamicpricing
    return render(request,'settings.html',{"fpi":fpi,"threshold":threshold,"totalfloors":totalfloors,"floorcapacity":floorcapacity,"dynamicpricing":dynamicpricing})

def assign_floor(user): #-----------------pass user obj here from entry function
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
@login_required(login_url="/login")
def entry(request):
    if request.method=='POST':
        username=request.user
        user_obj=User.objects.get(username=username)
        car_number=(request.POST['car_number']).lower()
        current_time=datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        floorassigned=assign_floor(request.user)
        if floorassigned==-1:
            messages.error(request,"No space available at any floor.. You may try after some time..")
            return redirect('/entry')
        total_capacity=user_obj.totalfloors*user_obj.floorcapacity
        total_cars_inside=user_obj.total_cars_inside
        if user_obj.dynamicpricing: #dynamic pricing is ON
            if(total_cars_inside<(total_capacity/2)):
                fpi=user_obj.fpi # <50%
            elif(total_cars_inside<(total_capacity*0.65)):
                fpi=2*user_obj.fpi # <65%
            elif(total_cars_inside<(total_capacity*0.8)):
                fpi=3*user_obj.fpi # <80%
            else:
                fpi=4*user_obj.fpi # >=80%
        else: #dynamic pricing is OFF
            fpi=user_obj.fpi
        new_entry= ParkingEntry.objects.create(username=username,entrytimestamp=current_time,car_number=car_number,floor_last_seen=0,floorassigned=floorassigned,fpi=fpi)
        new_entry.save()
        user_obj.total_cars_inside=total_cars_inside+1
        user_obj.save()
        messages.info(request,'Entry done!\n Car {} proceed to \nFLOOR NUMBER {}.'.format(car_number,floorassigned))
    return render(request,'entry.html')

def decrement_car_count(user,floor_number):
    floor=Floors.objects.get(username=user,floor_number=floor_number)
    floor.cars_parked-=1
    floor.save()
    user_obj=User.objects.get(username=user)
    user_obj.total_cars_inside=user_obj.total_cars_inside-1
    user_obj.save()

# for exit page
@login_required(login_url="/login")
def exit(request):
    if request.method=='POST':
        car_number=request.POST['car_number']
        try:
            last_entry=ParkingEntry.objects.get(username=request.user,car_number=car_number)
        except Exception as e:
            messages.error(request,"Encountered error: {}".format(e))
            return redirect('exit')
        time_difference=(datetime.datetime.now(pytz.timezone('Asia/Kolkata'))-last_entry.entrytimestamp).seconds
        # time_difference=type(last_entry.entrytimestamp)
        # settings=User.objects.get(username=request.user)
        fpi=last_entry.fpi
        if fpi==None or fpi=="NULL":
            messages.error(request,"Settings incomplete..")
            return redirect('exit')
        fine=0
        if last_entry.floorassigned!=-1 and last_entry.floor_last_seen!=last_entry.floorassigned:
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
@login_required(login_url="/login")
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
@login_required(login_url="/login")
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

# function to turn dynamic pricing ON & OFF
def change_dp_mode(request):
    if request.method=='POST':
        username=request.user
        user_obj=User.objects.get(username=username)
        user_obj.dynamicpricing=not(user_obj.dynamicpricing)
        user_obj.save()
        messages.info(request,"Dynamic Pricing mode changed..")
    return redirect('settings')