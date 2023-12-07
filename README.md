#   **COP4521 FINAL PROJECT**

##  Project Link: https://octobersradio.xyz/

### **This website implements several features:**

Sign in and register: Create an account to access the full functionality of the website.

Newsfeed: Browse the latest news articles pulled from Hacker News API.

Admin page: Manage the website content and settings (requires sign-in).

### To Use:

1) Clone the repository.

2) Download the requirements.txt file.

3) Set up Flask, Gunicorn, and Nginx.

4) Run gunicorn -w 3 flask_project:app.

### Links:

**Sign-up:** https://octobersradio.xyz/

**Home:** https://octobersradio.xyz/home

**Admin:** https://octobersradio.xyz/admin (requires sign-in)

### Technologies:

**Flask:** Web framework

**Gunicorn:** Web server gateway interface (WSGI)

**Nginx:** Web server

**Hacker News API:** Provides news articles

**Observatory score:** 80/100 

**Pylint score:** 6.99/10 

### **Additional resources:**

The main driver is the init.py file, which contains routes, functions, and database updates.

#### You can try accessing the newsfeed directly!: 

`curl -X GET https://octobersradio.xyz/newsfeed`

####  Configs are in the Configs Folder
