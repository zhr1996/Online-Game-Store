# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import Flask, render_template, request, session, redirect
from google.cloud import datastore
from google.oauth2 import id_token

import datetime
import sys
import requests

datastore_client = datastore.Client()
DEFAULT_KEY = 'Action'

# Attributes need to be stored
attributes = ['title', 'rating', 'platform', 'developer', 'year', 'price']

app = Flask(__name__)

app.secret_key = b'lkjadfsj009(*02347@!$&'

"""
User class I created, serves as a placeholder demonstrator
to store google user info
"""

# write new message to guestbook

# Store game to datastore


def store_game(game,
               # , username,
               # email,
               dt,
               kn):
    entity = datastore.Entity(key=datastore_client.key(kn.lower()))
    entity.update({
        'title': game["title"].strip(),
        'rating': game["rating"].strip(),
        'platform': game["platform"].strip(),
        'developer': game["developer"].strip(),
        'year': game["year"].strip(),
        'timestamp': dt,
        'price': game['price'].strip()
        # 'username': username,
        # 'email': email
    })

    datastore_client.put(entity)


# Store game to shopping cart
def store_to_cart(purchase, dt, kn):
    entity = datastore.Entity(key=datastore_client.key(kn.lower()))
    entity.update({
        'title': purchase['title'].lower(),
        'price': purchase['price'],
        'timestamp': dt
    })
    datastore_client.put(entity)


# Store purchase history
def store_purchase(purchase, dt, kn):
    entity = datastore.Entity(key=datastore_client.key(kn.lower()))
    entity.update({
        'title': purchase['title'].lower(),
        'price': purchase['price'],
        'timestamp': dt,
        'userID': purchase['useremail'].lower()
    })
    datastore_client.put(entity)

# Check if price is a number


def is_number(str):
    try:
        if str == 'NaN':
            return False
        float(str)
        return True
    except ValueError:
        return False
# index page
@app.route('/', methods=['GET'])
def root():
    if 'username' in session:
        username = session['username']
    else:
        username = ''

    if 'email' in session:
        useremail = session['email']
    else:
        useremail = ''

    print("username" + username)
    print("useremail" + useremail)

    errors = []
    return render_template('index.html', errors=errors)

# /add to cart
# Method : POST
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'email' in session:
        useremail = session['email']
    else:
        useremail = ""

    # If not logged in, let user login first
    if useremail == '':
        errors = []
        errors.append('Please log in first!')

        return render_template('index.html', errors=errors)
    else:
        print(useremail)
        print("list")
        print(request.form.getlist('games'))
        games = request.form.getlist('games')
        game_list = []
        query = datastore_client.query(kind=useremail)
        iter2 = query.fetch()
        for game in games:
            temp = game.split(",")  # split string
            temp = [sen.strip() for sen in temp]  # strip() string
            game_list.append(temp[:])

        # Convert the iterator to a list
        query_dict = []
        for game in iter2:
            query_dict.append(game)

        for game_li in game_list:
            flag = 1
            for game in query_dict:
                if game['title'].lower() == game_li[0].lower():
                    print(game['title'])
                    print(game_li[0])
                    flag = 0
                    break
            # add new game
            if flag == 1:
                purchase = {}
                purchase['title'] = game_li[0]
                purchase['price'] = float(game_li[-1])
                store_to_cart(purchase, datetime.datetime.now(), useremail)
        return render_template('index.html', errors=[])


# delete items in shopping cart
@app.route('/delete', methods=['POST'])
def delete_item():
    if 'email' in session:
        useremail = session['email']
    else:
        useremail = ""

    if useremail == '':
        errors = []
        errors.append('Please log in first!')

        return render_template('index.html', errors=errors)
    else:
        game_IDs = request.form.getlist("games")
        query = datastore_client.query(kind=useremail)
        query_iter = query.fetch()

        for entity in query_iter:
            if str(entity.id) in game_IDs:
                datastore_client.delete(entity.key)
    return redirect('/shopping-cart')

# view shopping history(not required)
@app.route('/shopping-history', methods=['GET'])
def view_history():
    if 'email' in session:
        useremail = session['email']
    else:
        useremail = ""

    if useremail == "":
        return render_template('index.html', errors=['Please log in first'])
    else:
        query = datastore_client.query(kind="history".lower())
        query_iter = query.fetch()
        history = []
        for entity in query_iter:
            temp = [entity['title'], str(entity['price']), str(
                entity['timestamp']), entity['userID']]
            item = ",".join(temp)
            entity['description'] = item
            history.append(entity)
        return render_template('shopping-history.html', history=history)


# view shopping cart
@app.route('/shopping-cart', methods=['get'])
def view_cart():
    if 'email' in session:
        useremail = session['email']
    else:
        useremail = ""

    if useremail == "":
        return render_template('index.html', errors=['Please log in first'])
    else:
        query = datastore_client.query(kind=useremail.lower())
        query_iter = query.fetch()
        games = []
        total_cost = 0
        for entity in query_iter:
            temp = [entity['title'], str(
                entity['price'])]
            result = ",".join(temp[:])
            entity['description'] = result
            games.append(entity)
            total_cost += entity['price']
        return render_template('shopping-cart.html', games=games, cost=total_cost)


# add new game into datastore
@app.route('/add', methods=['POST'])
def add():

    if (request.form['genre'] is ""):
        key_name = DEFAULT_KEY
    else:
        key_name = request.form['genre']

    game = {}
    for attribute in attributes:
        game[attribute] = request.form[attribute]

    attribute_empty = 0
    for attribute in attributes:
        if game[attribute] == "":
            attribute_empty = 1
        if attribute.lower() == "price":
            if not is_number(game[attribute]):
                return render_template('enter.html', errors=["Please enter a valid price"])

    if (attribute_empty == 1):
        errors = []
        errors.append("Please enter all the fields")
        return render_template('enter.html', errors=errors)
    else:
        store_game(game,
                   # username,
                   # useremail,
                   datetime.datetime.now(), key_name)
        return redirect("/")


# Display games
@app.route('/display', methods=['GET'])
def display():
    # results = []
    genre = request.args.get('genre')
    query = datastore_client.query(kind=genre.lower())
    query_iter = query.fetch()
    games = []
    for entity in query_iter:
        game_attribute = []
        for attribute in attributes:
            game_attribute.append(entity[attribute])
        result = ','.join(game_attribute[:])
        entity['description'] = result
        games.append(entity)

        # results.append(result)

    return render_template('display.html', Genre=genre, games=games)

# Check out
@app.route('/checkout', methods=['GET'])
def checkout():
    if 'email' in session:
        useremail = session['email']
    else:
        useremail = ""

    if useremail == '':
        errors = []
        errors.append('Please log in first!')

        return render_template('index.html', errors=errors)
    else:

        query = datastore_client.query(kind=useremail)
        query_iter = query.fetch()
        if not query_iter:
            return render_template('checkout.html', message="Please add items before check out")
        else:
            for entity in query_iter:
                purchase = {}
                datastore_client.delete(entity.key)
                purchase['title'] = entity['title']
                purchase['price'] = int(entity['price'])
                purchase['useremail'] = useremail.lower()
                store_purchase(purchase, datetime.datetime.now(),
                               "history")
            return render_template('checkout.html', message="Successed! Thank you for your purchase!")


# Enter new game info
@app.route('/enter', methods=['GET'])
def enter():
    genre = DEFAULT_KEY
    return render_template('enter.html', Genre=genre, errros=[])

# Search for games
@app.route('/search', methods=['GET', 'POST'])
def search():
    games = []
    errors = []
    if (request.method == 'POST'):

        # Use query to get all games from that genre
        genre = request.form['genre']
        if genre == "":
            return render_template('search.html', games=games, errors=['Please enter a genre'])
        query = datastore_client.query(kind=genre.lower())
        query_iter = query.fetch()
        games = []

        empty_flag = 1
        for attribute in attributes:
            if (request.form[attribute] != ""):
                empty_flag = 0

        if (empty_flag == 1):
            errors.append('Please at least enter one field')

        else:
            # Filtering, Compare criteria with all entities in the category, find if any is satisfied

            for entity in query_iter:
                flag = 1
                for attribute in attributes:
                    if (request.form[attribute] != "") and (request.form[attribute].lower() not in entity[attribute].lower()):
                        flag = 0
                        break
                    if (attribute == "year" and request.form[attribute] != "" and request.form[attribute] != entity[attribute]):
                        flag = 0
                        break
                if (flag == 1):
                    games.append(entity)

            for game in games:
                print(game)
                game_attribute = []
                for attribute in attributes:
                    game_attribute.append(game[attribute])
                result = ','.join(game_attribute[:])
                game['description'] = result

            if not games:
                errors.append('No result is found')

    return render_template('search.html', games=games, errors=errors)

# login user
@app.route('/login', methods=['POST'])
def login():
    # Decode the incoming data
    token = request.data.decode('utf-8')

    # Send to google for verification and get JSON return values
    verify = requests.get(
        "https://oauth2.googleapis.com/tokeninfo?id_token=" + token)

    # Use a session cookie to store the username and email

    session['username'] = verify.json()["name"]
    session['email'] = verify.json()["email"]

    return render_template('index.html', errors=[])

# logout user
@app.route('/logout', methods=['POST'])
def logout():

    # # Decode the incoming dataß
    # token = request.data.decode('utf-8')

    # # Send to google for verification and get JSON return values
    # verify = requests.get(
    #     "https://oauth2.googleapis.com/tokeninfo?id_token=" + token)

    # Use a session cookie to store the username and email
    print("reached")
    session.pop('username', None)
    session.pop('email', None)
    print("username")
    return redirect("/")


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.

    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
