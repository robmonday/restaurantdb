from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

app = Flask(__name__)

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


#Example API Endpoint (GET Request)
@app.route('/restaurant/<int:restaurant_id>/menu/JSON/')
def restaurantMenuJSON(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
	return jsonify (MenuItems=[i.serialize for i in items])  #here we 'jsonify' the returned output--instead of rendering an HTML template

#Quiz API Endpoint (GET Request)
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON/')
def restaurantMenuItemJSON(restaurant_id, menu_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	item = session.query(MenuItem).filter_by(id = menu_id).one()
	return jsonify (MenuItem=[item.serialize])

@app.route('/')
@app.route('/restaurant/')
@app.route('/restaurants/')
def showRestaurants():
	return "showRestaurants" #render_template('restaurants.html') #stub

@app.route('/restaurant/new/')
def newRestaurant():
	return "newRestaurant" #render_template('newRestaurant.html') #stub

@app.route('/restaurant/edit/')
def editRestaurant():
	return "editRestaurant" #render_template('editRestaurant.html') #stub

@app.route('/restaurant/delete/')
def deleteRestaurant():
	return "deleteRestaurant" #render_template('deleteRestaurant.html') #stub

@app.route('/restaurant/<int:restaurant_id>/')
@app.route('/restaurant/<int:restaurant_id>/menu/')
def restaurantMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id)
    return render_template('menu.html', restaurant=restaurant, items=items)

# Task 1: Create route for newMenuItem function here

@app.route('/restaurant/<int:restaurant_id>/menu/new/', methods=['GET','POST'])
def newMenuItem(restaurant_id):
	if request.method == 'POST':
		newItem = MenuItem(name=request.form['name'], price=request.form['price'], \
			course=request.form['course'], description=request.form['description'], \
			restaurant_id=restaurant_id)
		session.add(newItem)
		session.commit()
		flash('New menu item created')
		return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
	else:
		return render_template('newmenuitem.html', restaurant_id=restaurant_id)

# Task 2: Create route for editMenuItem function here

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

# Task 3: Create a route for deleteMenuItem function here

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