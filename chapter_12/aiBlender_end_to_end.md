# aiBlender, end-to-end

## 1. Objectives


&nbsp;
## 2. System architecture

&nsbp;
## 3. Install PostgreSQL database and vector-store 

While [PostgreSQL's office website](https://www.postgresql.org/docs/14/admin.html) 
provides details installation and administration guide, 
following is our steps to install postgre-sql, and start it up as Ubuntu system service. 

~~~
Step 1: Update System Packages
$ sudo apt update
$ sudo apt upgrade -y

Step 2: Install PostgreSQL
$ sudo apt install postgresql postgresql-contrib -y

# Verify Installation
$ sudo systemctl status postgresql

Step 3: Basic Post-Install Configuration
  # 1. Switch to the postgres User
  $ sudo -i -u postgres

  # 2. Set a Password for the postgres DB User
    Run the PostgreSQL CLI (psql):
  postgres$ psql
    -> ALTER USER postgres WITH PASSWORD 'your_secure_password';
    -> \q

  # 3. Create a new user (for testing purpose)
  postgres$ createuser --interactive --pwprompt robot
    Enter password for new role: 1234567890   
    Enter it again: 1234567890
    Shall the new role be a superuser? (y/n) y

  # 4. Create a new database (for testing purpose)
  postgres$ createdb --owner=robot robot_db  (Doesn't work)
  postgres$ CREATE DATABASE robot_db OWNER robot (Doesn't work)
  postgres$ exit

  $ sudo -i -u postgres createdb --owner=robot robot_db  (This one works)
~~~
