# aiBlender, end-to-end

## 1. Objectives


&nbsp;
## 2. System architecture


&nsbp;
## 3. Install PostgreSQL database and vector-store 

[PostgreSQL's office website](https://www.postgresql.org/docs/14/admin.html) 
provides details installation and administration guide.

To do it quickly, you can follow our steps to install postgre-sql, and start it up as a ubuntu system service. 

### 3.1 Install PostgreSQL

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

    Following are inside psql shell:
  postgres=# ALTER USER postgres WITH PASSWORD '1234567890';
  postgres=# \q

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


&nbsp;
### 3.2 Configure Networking

**Step 1. Edit the pg_hba.conf File**

1. Check the version of our PostgreSQL 
   ~~~
   $ ls /etc/postgresql/
     14
   ~~~

2. Edit the pg_hba.conf File, replace `<VERSION>` as `14`
   ~~~
   $ sudo vim /etc/postgresql/<VERSION>/main/pg_hba.conf
   ~~~

   Find the lines for local and host connections, and update to use `md5` for password authentication):
   ~~~
   # Local connections
   local      all      all                        md5
   # IPv4 local connections
   host       all      all      127.0.0.1/32      md5
   # IPv6 local connections
   host       all      all      ::1/128           md5
   ~~~

3. Add this line to allow access from your local network (replace 192.168.1.0/24 with your subnet):
   ~~~
   host       all      all     192.168.1.0/24     md5
   ~~~

**Step 2. Edit postgresql.conf to Listen for connections**

   ~~~
   $ sudo nano /etc/postgresql/<VERSION>/main/postgresql.conf
   ~~~

   Update the `listen_addresses` line to allow all interfaces:
   ~~~
   listen_addresses = '*'             # Default is 'localhost'
   ~~~
