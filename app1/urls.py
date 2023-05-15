from django.urls import path
from . import views

urlpatterns=[
    path('',views.index,name='index'),
    path('register',views.register,name='register'),
    path('login',views.login,name='login'),
    path('settings',views.settings,name='settings'),
    path('entry',views.entry,name='entry'),
    path('exit',views.exit,name='exit'),
    path('floor',views.floor,name='floor'),
    path('pay',views.pay,name='pay'),
    path('logout',views.logout,name='logout')
]