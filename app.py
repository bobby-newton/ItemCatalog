# Imports
import os
import random
import string
import datetime
import json
import httplib2
import requests
from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash, make_response
from flask import session as login_session
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from db_table_seed import Base, Catalogue, ListItem, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from login_decorator import login_required


# Flask Instance
app = Flask(__name__)

# Client ID
CLIENT_ID = json.loads(
        open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalogue Project"

# Database
# Connect to database
engine = create_engine('sqlite:///cataloguelist.db')
Base.metadata.bind = engine
# Create session
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Login Routing
# Login - Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" %  login_session['state']
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
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        # Todo try / catch - handle accounts.google.com not available
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '"style="width:300px;height:300px;border-radius:150px;"'
    output += '"-webkit-border-radius:150px;-moz-border-radius:150px;">'
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions
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


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's session.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        response = redirect(url_for('showCatalogues'))
        flash("You are now logged out")
        return response
    else:
        # If the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Catalogue Information
@app.route('/catalogue/<int:catalogue_id>/list/JSON')
def catalogueListJSON(catalogue_id):
    catalogue = session.query(Catalogue).filter_by(id=catalogue_id).one()
    items = session.query(ListItem).filter_by(
        catalogue_id=catalogue_id).all()
    return jsonify(ListItems=[i.serialize for i in items])


@app.route('/catalogue/<int:catalogue_id>/list/<int:list_id>/JSON')
def ListItemJSON(catalogue_id, list_id):
    List_Item = session.query(ListItem).filter_by(id=list_id).one()
    return jsonify(List_Item=List_Item.serialize)


@app.route('/catalogue/JSON')
def cataloguesJSON():
    catalogues = session.query(Catalogue).all()
    return jsonify(catalogues=[r.serialize for r in catalogues])


# Flask Routing
# Show all catalogues
@app.route('/')
@app.route('/catalogue/')
def showCatalogues():
    catalogues = session.query(Catalogue).order_by(asc(Catalogue.name))
    if 'username' not in login_session.keys():
        return render_template('publicCatalogues.html', catalogues=catalogues)
    else:
        return render_template('catalogues.html', catalogues=catalogues)


# Create a new catalogue
@app.route('/catalogue/new/', methods=['GET', 'POST'])
def newCatalogue():
    if 'username' not in login_session.keys():
        return redirect('/login')
    if request.method == 'POST':
        newCatalogue = Catalogue(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCatalogue)
        flash('New Catalogue %s Successfully Created' % newCatalogue.name)
        session.commit()
        return redirect(url_for('showCatalogues'))
    else:
        return render_template('newCatalogue.html')


# Edit a catalogue
@app.route('/catalogue/<int:catalogue_id>/edit/', methods=['GET', 'POST'])
def editCatalogue(catalogue_id):
    print("/catalogue/<int:catalogue_id>/edit")
    editedCatalogue = session.query(
        Catalogue).filter_by(id=catalogue_id).one()
    if 'username' not in login_session.keys():
        return redirect('/login')
    if editedCatalogue.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized"
        + "to edit this catalogue. Please create your own catalogue in order"
        + "to edit.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            print("catalogue name to edit: " + request.form['name'])
            editedCatalogue.name = request.form['name']
            flash('Catalogue Successfully Edited %s' % editedCatalogue.name)
            return redirect(url_for('showCatalogues'))
    else:
        return render_template('editCatalogue.html', catalogue=editedCatalogue)


# Delete a catalogue
@app.route('/catalogue/<int:catalogue_id>/delete/', methods=['GET', 'POST'])
def deleteCatalogue(catalogue_id):
    catalogueToDelete = session.query(
        Catalogue).filter_by(id=catalogue_id).one()
    if 'username' not in login_session.keys():
        return redirect('/login')
    if catalogueToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized"
        + "to delete this catalogue. Please create your own catalogue in order"
        + "to delete.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(catalogueToDelete)
        flash('%s Successfully Deleted' % catalogueToDelete.name)
        session.commit()
        return redirect(url_for('showCatalogues', catalogue_id=catalogue_id))
    else:
        return render_template(
            'deleteCatalogue.html', catalogue=catalogueToDelete)


# Show a catalogue item
@app.route('/catalogue/<int:catalogue_id>/')
@app.route('/catalogue/<int:catalogue_id>/list/')
def showList(catalogue_id):

    catalogue = session.query(Catalogue).filter_by(id=catalogue_id).one()
    creator = getUserInfo(catalogue.user_id)
    items = session.query(ListItem).filter_by(
        catalogue_id=catalogue_id).all()

    if ('username' not in login_session.keys()
    or creator.id != login_session['user_id']):
        return render_template(
            'publiclist.html',
            items=items,
            catalogue=catalogue,
            creator=creator)
    else:
        return render_template(
            'list.html',
            items=items,
            catalogue=catalogue,
            creator=creator)


# Create a new list item
@app.route('/catalogue/<int:catalogue_id>/list/new/', methods=['GET', 'POST'])
def newListItem(catalogue_id):
    if 'username' not in login_session.keys():
        return redirect('/login')
    catalogue = session.query(Catalogue).filter_by(id=catalogue_id).one()
    if login_session['user_id'] != catalogue.user_id:
        return "<script>function myFunction() {alert('You are not authorized"
        + "to add list items to this catalogue. Please create your own"
        + "catalogue in order to add items.');}</script><body"
        + "onload='myFunction()'>"
    if request.method == 'POST':
        newItem = ListItem(name=request.form['name'],
                           description=request.form['description'],
                           catalogue_id=catalogue_id,
                           user_id=catalogue.user_id)
        session.add(newItem)
        session.commit()
        flash('New List %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showList', catalogue_id=catalogue_id))
    else:
        return render_template('newlistitem.html', catalogue_id=catalogue_id)


# Edit a list item
@app.route(
    '/catalogue/<int:catalogue_id>/list/<int:list_id>/edit',
    methods=['GET', 'POST'])
def editListItem(catalogue_id, list_id):
    if 'username' not in login_session.keys():
        return redirect('/login')
    editedItem = session.query(ListItem).filter_by(id=list_id).one()
    catalogue = session.query(Catalogue).filter_by(id=catalogue_id).one()
    if login_session['user_id'] != catalogue.user_id:
        return "<script>function myFunction() {alert('You are not authorized"
        + "to edit list items to this catalogue. Please create your own"
        + "catalogue in order to edit items.');}</script><body"
        + "onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
        flash('List Item Successfully Edited')
        return redirect(url_for('showList', catalogue_id=catalogue_id))
    else:
        return render_template(
            'editlistitem.html',
            catalogue_id=catalogue_id,
            list_id=list_id,
            item=editedItem)


# Delete a list item
@app.route(
    '/catalogue/<int:catalogue_id>/list/<int:list_id>/delete',
    methods=['GET', 'POST'])
def deleteListItem(catalogue_id, list_id):
    if 'username' not in login_session.keys():
        return redirect('/login')
    catalogue = session.query(Catalogue).filter_by(id=catalogue_id).one()
    itemToDelete = session.query(ListItem).filter_by(id=list_id).one()
    if login_session['user_id'] != catalogue.user_id:
        return "<script>function myFunction() {alert('You are not authorized"
        + "to delete list items to this catalogue. Please create your own"
        + "catalogue in order to delete items.');}</script><body"
        + "onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('List Item Successfully Deleted')
        return redirect(url_for('showList', catalogue_id=catalogue_id))
    else:
        return render_template('deletelistitem.html', item=itemToDelete)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session.keys():
        if login_session['provider'] == 'google':
            gdisconnect()
        flash("You have successfully been logged out.")
        return redirect(url_for('showCatalogues'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCatalogues'))

# Important! Always at the end of file.
if __name__ == '__main__':
    app.secret_key = 'awesome_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
