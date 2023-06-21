# Multilevel Parking Management System
## Steps
1. Clone the repo
2. Make a virtual environment in the same location as the 'mpms' folder

   `python -m venv env`
3. `cd mpms`
4. Activate virtual environment

   `..\env\Scripts\activate` [for windows]  
   OR  `../env/bin/activate` [for linux]
5. `pip install -r requirements.txt`
6. `python manage.py makemigrations`
7. `python manage.py migrate`
8. Add a config.py file in the same location as that of manage.py file. It should contain passwords, etc. in the following format:

        #django secret key
        dsk='qqqqqqqqq'  

        #Razorpay API key [make a free account with Razorpay for this]
        key1 = 'aaaaaaaaa'   

        #Razorpay API  secret key [make a free account with Razorpay for this]
        key2 = 'bbbbbbbbb'   

        #the email id which will send mails to registered users
        email='abc@gmail.com'  
        
        # App password to your gmail [NOT the password of your google account, generate app password separately]
        passw='ccccccccc'   

         aws_access_key='AAAAAAAA'

         aws_secret_access_key='xxxxxxxxxxxxxx'
9. `python manage.py runserver` to start the development server
10. Use the web app
11. Quit the server with `CTRL+C` and deactivate virtual env with `deactivate`

Lastly, there is 1 open issue in this repository! If you would like to contribute, comment on the issue to show your interest and I'll assign it to you!
