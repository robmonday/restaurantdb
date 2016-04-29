from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User

app = Flask(__name__)

#Import libraries used in 3rd-party authentication
from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(open('client_secrets.json','r').read())['web']['client_id'] #this is how Google identifies our app
APPLICATION_NAME = "Restaurant Menu Application"

engine = create_engine('sqlite:///restaurantmenuwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token
@app.route('/login/')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


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

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

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

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user email exists, if not make a new user
    # user_records = session.query(User).filter_by(email=login_session['email']).all()
    # if (len(user_records)<1):
    # 	print "New user in database"
    # else:
    # 	print "Existing user in database"

    # Store user_id for login session:  see if user email exists, if not make a new user
    user_id = getUserID(login_session['email'])
    if not user_id:
    	user_id = createUser(login_session) 
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

def createUser(login_session):
	"""Create new user in database from login session, then return user ID"""
	newUser = User(name = login_session['username'], email = login_session['email'], picture = login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email = login_session['email']).one()
	return user.id

def getUserInfo(user_id):
	"""Pass in user ID, and function returns associated user object"""
	user = session.query(User).filter_by(id = user_id).one()
	return user

def getUserID(email):
	"""Pass in user email, and function returns user ID (if email exists in DB)"""
	try:
		user = session.query(User).filter_by(email = email).one()
		return user.id
	except:
		return None


@app.route('/restaurants/JSON/')
def restaurantsJSON():
	restaurants = session.query(Restaurant).all()
	return jsonify (Restaurants=[restaurant.serialize for restaurant in restaurants])

@app.route('/restaurant/<int:restaurant_id>/menu/JSON/')
def restaurantMenuJSON(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
	return jsonify (MenuItems=[i.serialize for i in items])

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON/')
def restaurantMenuItemJSON(restaurant_id, menu_id):
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	item = session.query(MenuItem).filter_by(id=menu_id).one()
	return jsonify (MenuItem=[item.serialize])

@app.route('/')
@app.route('/restaurant/')
@app.route('/restaurants/')
def showRestaurants():
	restaurants = session.query(Restaurant).all()
	return render_template('restaurants.html', restaurants=restaurants)
	# if createUser(login_session) == ??: # if user id of session == restaurant record owner then render owner template
	# 	return render_template('restaurants.html', restaurants=restaurants) 
	# else: #otherwise, just render the public template
	# 	return render_template('publicrestaurants.html', restaurants=restaurants)

@app.route('/restaurant/new/', methods=['GET','POST'])
def newRestaurant():
	if request.method == 'POST':
		newRest = Restaurant(name=request.form['name'], user_id=login_session['user_id'])
		session.add(newRest)
		session.commit()
		flash('New restaurant created')
		return redirect(url_for('showRestaurants'))
	else:
		return render_template('newRestaurant.html')

@app.route('/restaurant/<int:restaurant_id>/edit/', methods=['GET','POST'])
def editRestaurant(restaurant_id):
	editRest = session.query(Restaurant).filter_by(id=restaurant_id).one()
	if request.method == 'POST':
		editRest.name = request.form['name']
		session.add(editRest)
		session.commit()
		flash('Restaurant edited')
		return redirect(url_for('showRestaurants'))
	else:
		return render_template('editRestaurant.html', restaurant_id=restaurant_id, editRest=editRest)

@app.route('/restaurant/<int:restaurant_id>/delete/', methods=['GET','POST'])
def deleteRestaurant(restaurant_id):
	deleteRest = session.query(Restaurant).filter_by(id=restaurant_id).one()
	if request.method == 'POST':
		session.delete(deleteRest)
		session.commit()
		flash('Restaurant deleted')
		return redirect(url_for('showRestaurants'))
	else:
		return render_template('deleteRestaurant.html', restaurant_id=restaurant_id, deleteRest=deleteRest)

@app.route('/restaurant/<int:restaurant_id>/')
@app.route('/restaurant/<int:restaurant_id>/menu/')
def restaurantMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id)
    creator = getUserInfo(restaurant.user_id)
    if False: # if user id of session == restaurant record owner then render owner template
    	print "rendering owner template..."
    	return render_template('menu.html', restaurant=restaurant, items=items, creator = creator)
    else: # otherwise render public template
    	print "rendering public template..."
    	return render_template('publicmenu.html', restaurant=restaurant, items=items, creator = creator)

@app.route('/restaurant/<int:restaurant_id>/menu/new/', methods=['GET','POST'])
def newMenuItem(restaurant_id):
	if request.method == 'POST':
		newItem = MenuItem(name=request.form['name'], price=request.form['price'], \
			course=request.form['course'], description=request.form['description'], \
			restaurant_id=restaurant_id, user_id=login_session['user_id'])
		session.add(newItem)
		session.commit()
		flash('New menu item created')
		return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
	else:
		return render_template('newmenuitem.html', restaurant_id=restaurant_id)


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit/', methods=['GET','POST'])
def editMenuItem(restaurant_id, menu_id):
	editedItem = session.query(MenuItem).filter_by(id=menu_id).one()
	if request.method == 'POST':
		if request.form['name']:
			editedItem.name = request.form['name']
		if request.form['price']:
			editedItem.price = request.form['price']
		if request.form['course']:
			editedItem.course = request.form['course']
		if request.form['description']:
			editedItem.description = request.form['description']

		session.add(editedItem)
		session.commit()
		flash('Menu item edited')
		return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
	else:
		return render_template('editmenuitem.html', restaurant_id=restaurant_id, menu_id=menu_id, i=editedItem)


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete/', methods=['GET','POST'])
def deleteMenuItem(restaurant_id, menu_id):
    deletedItem = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
    	session.delete(deletedItem)
    	session.commit()
    	flash('Menu item deleted')    	
    	return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
    else:
    	return render_template('deletemenuitem.html', restaurant_id=restaurant_id, menu_id=menu_id, item=deletedItem)

if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host='0.0.0.0', port=5000)