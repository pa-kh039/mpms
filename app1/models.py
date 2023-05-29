from django.db import models
from django.contrib.auth.models import AbstractUser
from .manager import UserManager
# Create your models here.

#just adding columns by extending AbstractUser
# for writing own model from scratch, extend AbstractBaseUser
# custom user model banana padega to add extra columns for settings wali fields 
class User(AbstractUser):
    username=models.CharField(max_length=100,primary_key=True,default="NULL")
    email=models.EmailField(blank=False,unique=True)
    phone=models.CharField(max_length=10,blank=False)
    auth_token=models.CharField(max_length=100,default="NULL")
    is_verified=models.BooleanField(default=False)
    totalfloors=models.IntegerField(null=True,blank=True)
    fpi=models.FloatField(null=True,blank=True)  #if these field values are found empty/null while calculation then tell user to do settings first
    threshold=models.IntegerField(null=True,blank=True) 
    floorcapacity=models.IntegerField(null=True,blank=True) 
    dynamicpricing=models.BooleanField(default=False) #dp
    total_cars_inside=models.IntegerField(blank=False,default=0) #dp

    objects=UserManager()
    # REQUIRED_FIELDS=[]
    USERNAME_FIELD='username'

class ParkingEntry(models.Model):
    # find entry timestamp and make a column for that
    # is table ki primary key (user+entry timestamp) columns milake banegi
    # username=models.CharField(max_length=100,null=False,blank=False,default="NULL")
    username=models.ForeignKey(User,on_delete=models.CASCADE,blank=False,null=True)
    entrytimestamp=models.DateTimeField(null=False,blank=False)
    car_number=models.CharField(max_length=10,null=False,blank=False)
    floor_last_seen=models.IntegerField(blank=True,null=True)
    floorassigned=models.IntegerField(blank=False,default=-1)
    fpi=models.FloatField(blank=False,default=1) #dp
    # details=models.CharField(max_length=500)  #ye column pata nhi kis liye tha

class Floors(models.Model):
    # username=models.CharField(max_length=100,null=False,blank=False,default="NULL")
    username=models.ForeignKey(User,on_delete=models.CASCADE,blank=False,null=True)
    floor_number=models.IntegerField(blank=False)
    cars_parked=models.IntegerField(blank=False,default=0)