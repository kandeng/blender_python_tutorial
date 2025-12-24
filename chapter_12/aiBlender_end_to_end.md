# aiBlender, end-to-end

## 1. Objectives


&nbsp;
## 2. System architecture


&nbsp;
## 3. Install postgre-sql and pgvector

[PostgreSQL's office website](https://www.postgresql.org/docs/14/admin.html) 
provides details installation and administration guide.

To do it quickly, you can follow our steps to install postgre-sql, and start it up as a ubuntu system service. 

### 3.1 Install postgre-sql
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
### 3.2 Configure networking

**Step 1. Edit the pg_hba.conf file**

1. Check the version of our postgre-sql 
   ~~~
   $ ls /etc/postgresql/
     14
   ~~~

2. Edit the pg_hba.conf file, replace `<VERSION>` as `14`
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

**Step 2. Edit postgresql.conf to listen for connections**
   ~~~
   $ sudo vim /etc/postgresql/<VERSION>/main/postgresql.conf
   ~~~

   Update the `listen_addresses` line to allow all interfaces:
   ~~~
   listen_addresses = '*'             # Default is 'localhost'
   ~~~

**Step 3. Restart PostgreSQL to apply changes**
   ~~~
   $ sudo systemctl status postgresql
     ● postgresql.service - PostgreSQL RDBMS
         Loaded: loaded (/lib/systemd/system/postgresql.service; enabled; vendor preset: enabled)
         Active: active (exited) since Tue 2025-12-23 21:09:07 CST; 30min ago
        Process: 3940105 ExecStart=/bin/true (code=exited, status=0/SUCCESS)
       Main PID: 3940105 (code=exited, status=0/SUCCESS)
            CPU: 805us 
     Dec 23 21:09:07 robot-test systemd[1]: Starting PostgreSQL RDBMS...
     Dec 23 21:09:07 robot-test systemd[1]: Finished PostgreSQL RDBMS

   $ sudo systemctl restart postgresql
   $
   ~~~

&nbsp;
### 3.3 Install pgvector

**Step 1. Add the pgvector repository**

   ~~~
   # Add PG apt repo (if not already added)
   $ sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
   $ wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
   # sudo apt update
    
   # Install pgvector, replace <VERSION> with 14
   # sudo apt install postgresql-<VERSION>-pgvector -y
   ~~~

&nbsp;
**Step 2. Enable pgvector in the postgre-sql database**

1. Connect to the postgre-sql database and enable the extension
   ~~~
   $ psql -U robot -d robot_db -h localhost
     Password for user robot: 1234567890
     psql (14.20 (Ubuntu 14.20-0ubuntu0.22.04.1))
     SSL connection (protocol: TLSv1.3, cipher: TLS_AES_256_GCM_SHA384, bits: 256, compression: off)
     Type "help" for help.

   robot_db=# 
   ~~~

2. Run this SQL command, and verify
   ~~~
   robot_db=# CREATE EXTENSION IF NOT EXISTS vector;

   robot_db=# \dx     # Verify that "vector" column does exist.
                             List of installed extensions
        Name   | Version |   Schema   |                     Description                      
      ---------+---------+------------+------------------------------------------------------
       plpgsql | 1.0     | pg_catalog | PL/pgSQL procedural language
       vector  | 0.8.1   | public     | vector data type and ivfflat and hnsw access methods
      (2 rows)

   robot_db=# \q
   ~~~

&nbsp;
### 3.4 Uninstall postgre-sql and pgvector completely
~~~
$ sudo apt purge postgresql postgresql-contrib -y

$ sudo apt autoremove -y

# Delete data directories (CAUTION: irreversibly deletes all databases!)
$ sudo rm -rf /var/lib/postgresql/
~~~
