#!/usr/bin/env python2.7.12
# This modules contains all the routes for the functioning
# of the application


from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from flask import Flask, render_template, url_for,\
 redirect, flash, request, jsonify


app = Flask(__name__)

# Load Google sign-in API client ID
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog Application"

# Connect to database and create a database session
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# ============================
# Login routing
# ============================
# Login - Create anti-forgery state token


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# GConnect


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    print result

    # If there was an error in the access token info, abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user
    google_id = credentials.id_token['sub']
    if result['user_id'] != google_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's"), 401)
        print "Token's client ID does not match app's"
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_google_id = login_session.get('google_id')
    if stored_access_token is not None and google_id == stored_google_id:
        response = make_response(json.dumps('Current user is already connected'
                                            ), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use
    login_session['access_token'] = credentials.access_token
    login_session['google_id'] = google_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if the user exists. If it doesn't, make a new one.
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    # Show a welcome screen upon successful login
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;\
    -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print "Done!"
    return output

# GDisconnect
# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/logout')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']

    result = requests.post(url='https://accounts.google.com/o/oauth2/revoke',
                           params={
                               'token': access_token,
                               'client_id': CLIENT_ID,
                               'client_secret': 'zCyqDf3J7hZk7pW8GBQcHC6F'
                           },
                           headers={
                               'content-type':
                                   'application/x-www-form-urlencoded;'
                                   ' charset=utf-8'
                           })

    print('result is ')
    print(result)

    if result.status_code == 200:
        del login_session['access_token']
        del login_session['google_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps
                                 ('Failed to revoke token for given user.',
                                  400))
        response.headers['Content-Type'] = 'application/json'
        return response

# User helper functions for creating new user


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# ==================================
# JSON Endpoints
# ==================================
# Making API end point for categories


@app.route('/catalog/JSON/')
def catalogJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])

# Make API end point for items for each category


@app.route('/catalog/<int:category_id>/items/JSON/')
def itemsJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(CatalogItems=[i.serialize for i in items])

# Making API end point for each item


@app.route('/catalog/<int:category_id>/item/<int:item_id>/JSON/')
def catalog_item_json(category_id, item_id):
    if exists_category(category_id) and exists_item(item_id):
        item = session.query(Item)\
               .filter_by(id=item_id, category_id=category_id).first()
        if item is not None:
            return jsonify(item=item.serialize)
        else:
            return jsonify(
                error='item {} does not belong to category {}.'
                .format(item_id, category_id))
    else:
        return jsonify(error='The item or the category does not exist.')
# ===========================
# Item Catalog Pages
# ===========================
# Show all catalog categories


@app.route('/')
@app.route('/catalog/')
@app.route('/catalog/items/')
def showCatalog():
    categories = session.query(Category).all()
    items = session.query(Item).limit(5)
    return render_template('catalog.html', categories=categories, items=items)

# Add new categories


@app.route('/catalog/category/new/', methods=['GET', 'POST'])
def addCategory():
    if 'username' not in login_session:
        flash("Please log in to continue")
        return redirect(url_for('showLogin'))
    elif request.method == 'POST':
        if request.form['new-category-name'] == '':
            flash('The field cannot be empty')
            return redirect(url_for('showCatalog'))

        category = session.query(Category).\
            filter_by(name=request.form['new-category-name']).first()
        if category is not None:
            flash('The entered category already exists.')
            return redirect(url_for('addCategory'))

        newCategory = Category(
            name=request.form['new-category-name'],
            user_id=login_session['user_id'])
        session.add(newCategory)
        session.commit()
        flash('New category %s successfully created!' % newCategory.name)
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newCategory.html')

# Show all items for a specific category using category id


@app.route('/catalog/<int:category_id>/')
@app.route('/catalog/<int:category_id>/items/')
def showItems(category_id):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    return render_template('catalogItems.html', category=category,
                           categories=categories, items=items)

# Add new items


@app.route('/catalog/item/new/', methods=['GET', 'POST'])
def addItem():
    if 'username' not in login_session:
        flash("Please log in to continue")
        return redirect(url_for('showLogin'))
    elif request.method == 'POST':
        item = session.query(Item).filter_by(name=request.form['name']).first()
        if item:
            if item.name == request.form['name']:
                flash('The item already exists in the database!')
                return redirect(url_for("addItem"))
        newItem = Item(
            name=request.form['name'],
            category_id=request.form['category'],
            description=request.form['description'],
            user_id=login_session['user_id']
            )
        session.add(newItem)
        session.commit()
        flash('New item successfully created!')
        return redirect(url_for('showCatalog'))
    else:
        items = session.query(Item).\
                filter_by(user_id=login_session['user_id']).all()
        categories = session.query(Category).\
            filter_by(user_id=login_session['user_id']).all()
        return render_template('newItem.html', items=items,
                               categories=categories)

# Check if the item exists in the database


def exists_item(item_id):
    item = session.query(Item).filter_by(id=item_id).first()
    if item is not None:
        return True
    else:
        return False

# Check if the category exists in the database


def exists_category(category_id):
    category = session.query(Category).filter_by(id=category_id).first()
    if category is not None:
        return True
    else:
        return False

# Show item by ID


@app.route('/catalog/item/<int:item_id>')
def showItemById(item_id):
    if exists_item(item_id):
        item = session.query(Item).filter_by(id=item_id).first()
        category = session.query(Category)\
            .filter_by(id=item.category_id).first()
        owner = session.query(User).filter_by(id=item.user_id).first()
        return render_template(
            "itemById.html",
            item=item,
            category=category,
            owner=owner
        )
    else:
        flash('We are unable to process your request right now.')
        return redirect(url_for('showCatalog'))

# Edit existing item


@app.route("/catalog/item/<int:item_id>/edit/", methods=['GET', 'POST'])
def editItem(item_id):
    if 'username' not in login_session:
        flash("Please log in to continue.")
        return redirect(url_for('showLogin'))

    if not exists_item(item_id):
        flash("We are unable to process your request right now.")
        return redirect(url_for('showCatalog'))

    item = session.query(Item).filter_by(id=item_id).first()
    if login_session['user_id'] != item.user_id:
        flash("You were not authorised to access that page.")
        return redirect(url_for('showCatalog'))

    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        if request.form['category']:
            item.category_id = request.form['category']
        session.add(item)
        session.commit()
        flash('Item successfully updated!')
        return redirect(url_for('editItem', item_id=item_id))
    else:
        categories = session.query(Category).\
            filter_by(user_id=login_session['user_id']).all()
        return render_template(
            'editItem.html',
            item=item,
            categories=categories
        )

# Delete existing item


@app.route("/catalog/item/<int:item_id>/delete/", methods=['GET', 'POST'])
def deleteItem(item_id):
    if 'username' not in login_session:
        flash("Please log in to continue.")
        return redirect(url_for('showLogin'))

    if not exists_item(item_id):
        flash("We are unable to process your request right now.")
        return redirect(url_for('showCatalog'))

    item = session.query(Item).filter_by(id=item_id).first()
    if login_session['user_id'] != item.user_id:
        flash("You were not authorised to access that page.")
        return redirect(url_for('showCatalog'))

    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash("Item successfully deleted!")
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteItem.html', item=item)

# Edit category


@app.route("/catalog/category/<int:category_id>/edit/",
           methods=['GET', 'POST'])
def editCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).first()

    if 'username' not in login_session:
        flash("Please log in to continue.")
        return redirect(url_for('showLogin'))

    if not exists_category(category_id):
        flash("We are unable to process your request right now.")
        return redirect(url_for('showCatalog'))

    if login_session['user_id'] != category.user_id:
        flash("You are unauthorised to access that page.")
        return redirect(url_for('showCatalog'))

    if request.method == 'POST':
        if request.form['name']:
            category.name = request.form['name']
            session.add(category)
            session.commit()
            flash('Category successfully updated!')
            return redirect(url_for('showCatalog', category_id=category.id))
    else:
        return render_template('editCategory.html', category=category)

# Delete category


@app.route("/catalog/category/<int:category_id>/delete/",
           methods=['GET', 'POST'])
def deleteCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).first()

    if 'username' not in login_session:
        flash("Please log in to continue.")
        return redirect(url_for('showLogin'))

    if not exists_category(category_id):
        flash("We are unable to process your request right now.")
        return redirect(url_for('showCatalog'))

    if login_session['user_id'] != category.user_id:
        flash("We are unable to process your request right now.")
        return redirect(url_for('showCatalog'))

    if request.method == 'POST':
        session.delete(category)
        session.commit()
        flash("Category successfully deleted!")
        return redirect(url_for('showCatalog'))
    else:
        return render_template("deleteCategory.html", category=category)


if __name__ == '__main__':
    app.secret_key = 'item_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000, threaded=False)
