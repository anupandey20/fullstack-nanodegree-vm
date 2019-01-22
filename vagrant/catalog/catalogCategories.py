from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker 
from database_setup import Category, Base, Item, User
 
engine = create_engine('sqlite:///itemcatalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
user1 = User(name="Anupama", email="anu.pandey20@gmail.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(user1)
session.commit()

#Items for Soccer
category1 = Category(user_id=1, name = "Sports")

session.add(category1)
session.commit()

category2 = Category(user_id=1, name="Books")
session.add(category2)
session.commit

category3 = Category(user_id=1, name="Clothing")
session.add(category3)
session.commit()

category4 = Category(user_id=1, name="Electronics")
session.add(category4)
session.commit()

category5 = Category(user_id=1, name="Food")
session.add(category5)
session.commit()

# Populate a category with items for testing
# Using different users for items also

item1 = Item(user_id=1, name="Soccer",
               #date=datetime.datetime.now(),
               description="Game played on field between 2 teams of 11 players",
               category_id=1)

session.add(item1)
session.commit()

item2 = Item(user_id=1, name="Hockey",
               #date=datetime.datetime.now(),
               description="A team game played between two teams of eleven players each using hooked sticks",
               category_id=1)

session.add(item2)
session.commit()

item3 = Item(user_id=1, name="Lacrosse",
               #date=datetime.datetime.now(),
               description="A team sport played with a lacrosse stick and a lacrosse ball",
               category_id=1)

session.add(item3)
session.commit()

item4 = Item(user_id=1, name="Basketball",
               #date=datetime.datetime.now(),
               description="A handball game usually played by two teams of five players on the court",
               category_id=1)

session.add(item4)
session.commit()

item5 = Item(user_id=1, name="Baseball",
               #date=datetime.datetime.now(),
               description="A bat-and-ball game played between two opposing teams who take turns batting and fielding",
               category_id=1)

session.add(item5)
session.commit()

item6 = Item(user_id=1, name="Skiing",
               #date=datetime.datetime.now(),
               description="Travelling over snow on skis",
               category_id=1)

session.add(item6)
session.commit()


# Added items for category_id 2

item1 = Item(user_id=1, name="Harry Potter",
               #date=datetime.datetime.now(),
               description="Book by J. K. Rowling",
               category_id=2)

session.add(item1)
session.commit()

item2 = Item(user_id=1, name="Junie B Jones",
               #date=datetime.datetime.now(),
               description="Book by Barbara park",
               category_id=2)

session.add(item2)
session.commit()

item3 = Item(user_id=1, name="Dogman",
               #date=datetime.datetime.now(),
               description="Book by Dav Pilkey",
               category_id=2)

session.add(item3)
session.commit()

item4 = Item(user_id=1, name="Goodnight moon",
               #date=datetime.datetime.now(),
               description="Book by Margaret Brown",
               category_id=2)

session.add(item4)
session.commit()

item5 = Item(user_id=1, name="The very hungry caterpillar",
               #date=datetime.datetime.now(),
               description="Book by Eric Carle",
               category_id=2)

session.add(item5)
session.commit()

item6 = Item(user_id=1, name="The cat in the hat",
               #date=datetime.datetime.now(),
               description="Book by Dr. Seuss",
               category_id=2)

session.add(item6)
session.commit()


#item2 = Item(name = "Cleats", description = "The shoes", title = "Soccer cleats", category = category1)

#session.add(item2)
#session.commit()


#item1 = Item(name = "Balls", description = "The balls", title = "Soccer balls", category = category1)

#session.add(item1)
#session.commit()

#item2 = Item(name = "Shin guards", description = "Protective shin guards", title = "The Shin guards", category = category1)

#session.add(item2)
#session.commit()

#item3 = Item(name = "Gloves", description = "The gloves", title = "The Goalkeeper gloves", category = category1)

#session.add(item3)
#session.commit()





#Items for Basketball
#category2 = Category(name = "Basketball")

#session.add(category2)
#session.commit()


#item1 = Item(name = "Basketball net", description = "The basketball net", title = "Basketball net", category = category2)

#session.add(item1)
#session.commit()




print "added catalog items!"
