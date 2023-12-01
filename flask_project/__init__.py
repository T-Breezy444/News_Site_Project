import json
import time
import datetime
from os import environ as env
from functools import wraps
import requests
from jwt import algorithms, decode
from os import environ as env
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, jsonify, render_template, url_for, flash, redirect, session, request
from flask_talisman import Talisman
from models import db, Post, User

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(app)
Talisman(app, force_https=False) 

with app.app_context():
    db.create_all()

oauth = OAuth(app)

oauth.register(
   "auth0",
   client_id=env.get("AUTH0_CLIENT_ID"),
   client_secret=env.get("AUTH0_CLIENT_SECRET"),
   client_kwargs={
       "scope": "openid profile email",
   },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

# Set the Hacker News API endpoint
HN_API_ENDPOINT = "https://hacker-news.firebaseio.com/v0"

# Define a function to fetch the top 30 news stories
def get_top_30_news_stories():
    response = requests.get(f"{HN_API_ENDPOINT}/topstories.json?print=pretty")  # Include print=pretty
    article_ids = json.loads(response.content)

    top_30_news_stories = []
    for article_id in article_ids[:30]:
        response = requests.get(f"{HN_API_ENDPOINT}/item/{article_id}.json?print=pretty")  # Include print=pretty
        article = json.loads(response.content)

        # Add the url key to the article
        article["url"] = response.url

        top_30_news_stories.append(article)

    return top_30_news_stories
def save_user_to_database(user):
    existing_user = User.query.filter_by(email=user['email']).first()
    if not existing_user:
        new_user = User(
            email=user['email'],
            role=user['role']
        )
        db.session.add(new_user)
    else:
        existing_user.role = user['role']
        # Update other fields if necessary
    db.session.commit()

def save_article_to_database(article):
    # Check if the article with the given ID already exists in the database
    existing_post = Post.query.filter_by(id=article['id']).first()

    if not existing_post:
        # If the article doesn't exist, create a new Post instance and add it to the database
        new_post = Post(
            id=article.get('id', None),
            title=article.get('title', None),
            author=article.get('by', 'N/A'),
            likes=0,
            # Add other fields you want to save
        )
        db.session.add(new_post)
        db.session.commit()

def populate_database_with_recent_news():
    top_30_news_stories = get_top_30_news_stories()
    for article in top_30_news_stories:
        save_article_to_database(article)
        
# Define a function to convert news stories to JSON format
def convert_news_stories_to_json(top_30_news_stories):
    json_data = {
        "news_items": []
    }
    for article in top_30_news_stories:
        json_data["news_items"].append({
            "by": article.get("by", None),
            "descendants": article.get("descendants", None),
            "id": article.get("id", None),
            "kids": article.get("kids", []),
            "score": article.get("score", None),
            "text": article.get("text", None),
            "time": article.get("time", None),
            "title": article.get("title", None),
            "type": article.get("type", None),
            "url": article.get("url", None),
        })

    return json.dumps(json_data, indent=4)  # Use indent=4 for pretty-printing

# Define a route to serve the top 30 news stories in JSON format
@app.route("/newsfeed")
def get_top_30_news_stories_in_json_format():
    top_30_news_stories = get_top_30_news_stories()
    json_data = convert_news_stories_to_json(top_30_news_stories)

    return json_data

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login"))
        
        print(session.get('user'))
        
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    return redirect("/home")

@app.route("/home")
def display_recent_news():
    # Populate the database with recent news before displaying
    populate_database_with_recent_news()

    # Fetch news items from the database
    news_items = Post.query.all()

    return render_template('home.html', news_items=news_items)

@app.route('/login')
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True))

@app.route('/callback', methods=["GET","POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session['user'] = token
    return redirect('/adduser')

@app.route("/register")
def register():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True),
        prompt="signup"
    )

@app.route("/users")
def users():
    # Retrieve all users from the database
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route("/logout")
@require_login
def logout():
    session.clear()
    return redirect(url_for("user"))

@app.route("/about")
def about():
	return render_template('about.html', title='About')

@app.route("/adduser")
def user1():
    # Get the user data from the session
    user_session = session.get('user')
    if not user_session:
        return redirect("/home")

    id_token = user_session.get('id_token', None)
    if not id_token:
        return redirect("/home")

    # Decode the id_token to get the user data
    claims = decode(id_token, algorithms=["RS256"], options={"verify_signature": False})

    # Create a user dictionary with the email from the decoded token and a role
    user = {
        'email': str(claims['email']),
        'role': 'Admin'
        # Add other fields you want to save
    }

    print(f"Email: {user['email']}, Role: {user['role']}")

    # Call the save_user_to_database function
    save_user_to_database(user)

    return redirect("/user")


@app.route("/user")
@require_login
def user():
    user = session.get('user')
    id_token = user.get('id_token', None)
    if not id_token:
        return redirect("/home")

    claims = decode(id_token, algorithms=["RS256"], options={"verify_signature": False})

    return render_template("user.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))


@app.route("/like_post", methods=["POST"])
def like_post():
    post_id = request.form.get('post_id')
    post = Post.query.get(post_id)
    if post:
        post.likes += 1
        db.session.commit()
    return redirect("/home")

@app.route("/dislike_post", methods=["POST"])
def dislike_post():
    post_id = request.form.get('post_id')
    post = Post.query.get(post_id)
    if post:
        post.likes -= 1
        db.session.commit()
    return redirect("/home")

@app.route("/admin")
@require_login
def admin():
    posts = Post.query.all()  # Query all posts
    users = User.query.all()  # Query all users
    return render_template('admin.html', posts=posts, users=users)

@app.route("/remove_user", methods=["POST"])
def remove_user():
    user_id = request.form.get('user_id')
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect("/admin")

@app.route("/remove_post", methods=["POST"])
def remove_post():
    post_id = request.form.get('post_id')
    post = Post.query.get(post_id)
    if post:
        db.session.delete(post)
        db.session.commit()
    return redirect("/admin")

@app.route("/remove_likes", methods=["POST"])
def remove_likes():
    post_id = request.form.get('post_id')
    post = Post.query.get(post_id)
    if post:
        post.likes = 0
        db.session.commit()
    return redirect("/admin")

# Start the web server
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=env.get("PORT", 3000), debug=True)
