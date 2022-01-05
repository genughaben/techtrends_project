import logging
import sys
from logging.config import dictConfig
from datetime import datetime
import sqlite3

from flask import Flask, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
from enums.ResponseType import ResponseType
from enums.Endpoints import Endpoints

# logging.basicConfig(filename="app.log", level=logging.DEBUG)



dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    },'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})


# Create a timestamp for logging
def _get_timestamp():
    return '{:%Y-%m-%d %H:%M:%S}'.format(datetime.now())


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    app.config["connections_count"] += 1
    return connection


# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute(
        'SELECT * FROM posts WHERE id = ?',
        (post_id,)
    ).fetchone()
    connection.close()
    return post


# Define the Flask application
app = Flask(__name__)
app.config["connections_count"] = 0
app.config['SECRET_KEY'] = 'your secret key'


# Define the main route of the web application
@app.route('/')
def index():
    app.logger.info(f"{_get_timestamp()} -  {Endpoints.INDEX.value} endpoint was reached")
    connection = get_db_connection()
    posts = connection.execute(
        'SELECT * FROM posts'
    ).fetchall()
    connection.close()
    return render_template('index.html', posts=posts)


# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.error(f"{_get_timestamp()} -  {Endpoints.POST.value} endpoint was reached: "
                         f"no article was found (404)")
        return render_template('404.html'), 404
    else:
        app.logger.info(f"{_get_timestamp()} -  {Endpoints.POST.value} endpoint was reached: "
                        f"article: {post['title']} retrieved")
        return render_template('post.html', post=post)


# Define the About Us page
@app.route('/about')
def about():
    app.logger.info(f"{_get_timestamp()} -  {Endpoints.ABOUT.value} endpoint was reached and page retrieved")
    return render_template('about.html')


# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
            app.logger.error(f"{_get_timestamp()} -  {Endpoints.CREATE.value} endpoint was reached: "
                             f"could not create - title missing")
        else:
            connection = get_db_connection()
            connection.execute(
                'INSERT INTO posts (title, content) VALUES (?, ?)',
                (title, content))
            connection.commit()
            connection.close()
            app.logger.info(f"{_get_timestamp()} -  {Endpoints.CREATE.value} endpoint was reached: "
                            f"article: {title} was created")
            return redirect(url_for('index'))

    return render_template('create.html')


# Check if app is running
@app.route("/healthz")
def health():
    app.logger.info(f"{_get_timestamp()} -  {Endpoints.HEALTH.value} endpoint was reached")
    return app.response_class(
        response=json.dumps({"result": "OK - healthy"}),
        status=200,
        mimetype='application/json'
    )


# Get the number of connections to the database
@app.route("/metrics")
def metrics():
    try:
        connection = get_db_connection()
        posts_count = connection.execute(
            'SELECT count(*) FROM posts'
        ).fetchone()[0]
        connection.close()
        app.logger.info(f"{_get_timestamp()} -  {Endpoints.METRICS.value} endpoint was reached, metrics retrieved")
    except ConnectionError:
        posts_count = 0
        app.logger.error(f"{_get_timestamp()} -  {Endpoints.METRICS.value} endpoint was reached, connection error")
    except:
        app.logger.error(f"{_get_timestamp()} -  {Endpoints.METRICS.value} endpoint was reached, unknown error")
        posts_count = 0

    return app.response_class(
        response=json.dumps({
            "status": ResponseType.SUCCESS.value,
            "data": {"db_connection_count": app.config["connections_count"], "posts_count": posts_count}
        }),
        status=200,
        mimetype='application/json'
    )


# start the application on port 3111
if __name__ == "__main__":
    # capture logs at sys.stdout and sys.stderr
    app.logger.addHandler(logging.StreamHandler(sys.stdout))
    app.logger.addHandler(logging.StreamHandler(sys.stderr))
    app.logger.addHandler(logging.FileHandler(filename="app.log"))
    app.logger.setLevel(logging.DEBUG)
    app.run(host='0.0.0.0', port='3111')
