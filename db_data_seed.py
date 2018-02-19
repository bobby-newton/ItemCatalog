from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_table_seed import Catalogue, Base, ListItem, User

engine = create_engine('sqlite:///cataloguelist.db')
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

# Import users from users.csv
f = open("data/users.csv", "r")

# Create mappings from first line
line = f.readline()
line = line.replace("\n","")
headers = line.split(",")
indexes = {}
i=0
for header in headers:
    indexes[header]=i
    i=i+1


user_id = indexes['user_id']
name = indexes['name']
email = indexes['email']
picture = indexes['picture']

# Iterate line by line
for line in f:
    line = line.replace("\n","")
    # Create user
    user = line.split(",")
    dbUser = User(id=user[user_id],name=user[name], email=user[email], picture=user[picture])
    session.add(dbUser)
    session.commit()

# Close the file
f.close()

# Import catalogues from catalogues.csv
f = open("data/catalogues.csv", "r")

# Create mappings from first line
line = f.readline()
line = line.replace("\n","")
headers = line.split(",")
indexes = {}
i=0
for header in headers:
    indexes[header]=i
    i=i+1

catalogue_id = indexes['catalogue_id']
name = indexes['name']
user_id = indexes['user_id']

# Iterate line by line
for line in f:
    line = line.replace("\n","")
    # Create catalogue
    catalogue=line.split(",")
    dbCatalogue = Catalogue(id=catalogue[catalogue_id],
                              name=catalogue[name], user_id=catalogue[user_id])
    session.add(dbCatalogue)
    session.commit()

# Close the file
f.close()

# Import items from items.csv
f = open("data/items.csv", "r")

# Create mappings from first line
line = f.readline()
line = line.replace("\n","")
headers = line.split(",")
indexes = {}
i=0
for header in headers:
    indexes[header]=i;
    i=i+1

item_id = indexes['item_id']
user_id = indexes['user_id']
name = indexes['name']
description = indexes['description']
catalogue_id = indexes['catalogue_id']

# Iterate line by line
for line in f:
    line = line.replace("\n","")
    item=line.split(",")
    print(item)
    dbItem = ListItem(id=item[item_id],user_id=item[user_id],
                         name=item[name], description=item[description],
                         catalogue_id=item[catalogue_id])
    session.add(dbItem)
    session.commit()

# Close the files
f.close()


print ("added catalogue items!")
