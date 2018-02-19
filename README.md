**Item Catalogue Web Application**
*This web app is a project for the Udacity Full Stack Web Developer NanoDegree.*
*Author: Bobby Newton*

**About**

This project is a RESTful web application utilising the Flask framework which accesses a SQL database that
populates Catalogues and the Catalogue List Items.
OAuth2 provides third party authentication.
Current OAuth2 is implemented using Google Accounts.

**Skills**
1: Python
2: HTML
3: CSS
4: OAuth2
5: Flask Framework
6: JSON
7: SQL
8: SQLAlchemy
9: Bootstrap Framework

**Dependencies**
[VirtualBox](https://www.virtualbox.org/wiki/Download_Old_Builds_5_1)
[Vagrant](https://www.vagrantup.com/downloads.html) 
[Udacity Project Vagrantfile](https://github.com/udacity/fullstack-nanodegree-vm)

**Installation**
1: Follow the Dependency links and install  VirtualBox and Vagrant. 
2: Clone the Udacity Project Vagrantfile
3: Go to the Vagrant directory and either clone this folder or download and place the zip.
4: Run Vagrant and find the Vagrant directory.
5: Launch Vagrant (Vagrant Up)
6: Log into Vagrant (Vagrant SSH)
7: Head into Vagrant (cd Vagrant)
8: Run sudo pip install requests to install the app imports which are not part of the VM.
9: Head into the /catalog file (cd /catalog)
9: Setup the Web App Table Database: python db_table_seed.py
10: Populate the Database with the fake item data: python db_data_seed.py
11: Run the web application: python app.py
12: Access the web application locally: http://localhost:5000/ (internet network required for full functionality of services such as Google Authentication.

**Google Login**
1: Go to the [Google Developer Console](https://developers.google.com/)
2: Sign up or Log In
3: Go to Credentials
4: Create Credentials > OAuth Client ID
5: Select Web application
6: Enter name "item catalogue project"
7: Create Authorised JavaScript origins = 'http://localhost:5000'
8: Create Authorised redirect URIs = 'http://localhost:5000/login' & 'http://localhost:5000/gconnect'
9: Select Create
10: Copy the Client ID and paste it into the data-clientid in login.html
11: On the Dev Console Select Download JSON
12: Rename JSON file to client_secrets.json
13: Place JSON file in the same directory as app.py
14: Good to go!! 

**JSON Endpoints**
The following Endpoints are open to the public:
Catalogue 
Catalogue: /catalogue/JSON - Displays all Catalogues
Catalogue List Items: /catalogue/catalogue_id/list/JSON - Displays Items for a specific Catalogue.
Catalogue Item: / catalogue/catalogue_id/list/list_id/JSON - Displays specific Catalogue Item.

**Extra Development Files:**
fb_client_secrets.json - This file is here for a template for the client secret information if Facebook OAuth is to be implemented at any point.
login_decorator.py - This file is for the purpose of added / extra authentication purposes, which is a display of the ability of different authentication purposes. @login_required under the @app.route is placed within app files if this was to be used.

**Must Read:**
The database fake items can only be edited or deleted by the creator. To ensure fast and easy changes to the database, the files have been made as csv files. These can be opened and edited using Microsoft Excel.
You can open the database files and change the creator ID matching your own once you have logged in using Google Authentication. 
The purpose of the fake catalogue is to fill up the database and show the display of catalogues and items. Once logged in you may however create your own catalogue and then create and edit or delete items that you have made.

***Have Fun!!***




