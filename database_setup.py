
# Configuration Code
import os
import sys 
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()
# Configuration Code

# Class Code
class Restaurant(Base):
	__tablename__ = 'restaurant' # Table Name
	# Mapper Code
	name = Column(String(80), nullable = False)
	id = Column(Integer, primary_key = True)
	# Mapper Code

class MenuItem(Base):
	__tablename__ = 'menu_item' # Table Name
	# Mapper Code
	name = Column(String(80), nullable = False)
	id = Column(Integer, primary_key = True)
	course = Column(String(250))
	description = Column(String(250))
	price = Column(String(8))
	restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
	restaurant = relationship(Restaurant)
	# Mapper Code
# Class Code

# Configuration Code
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.create_all(engine)
# Configuration Code


