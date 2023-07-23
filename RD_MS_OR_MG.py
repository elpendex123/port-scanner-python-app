# Port Scanner
# Author: Raisal Islam
# Version: Beta Version 0.07
#
# Description:
# The Port Scanner is a Python script designed to scan the open ports of specified destinations. It utilizes multiple
# database options, including MySQL, Redis, Oracle, and MongoDB, to store the scan results. The script supports
# multithreading for efficient scanning.
import mysql.connector
import configparser
import cx_Oracle
import redis
import socket
import threading
from queue import Queue
import uuid
import os
from pymongo import MongoClient

# Define the unique identifier for this scan
scan_id = str(uuid.uuid4())

# Function to create a new MySQL connection
def connect_mysql():
    try:
        host = "192.168.56.102"  
        port = 3306  
        user = "Taslema"  
        password = "Taslema71!"  

        # Establish a new MySQL connection
        mysql_db = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password
        )
        return mysql_db
    except (mysql.connector.Error, ConnectionError, TimeoutError) as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Function to establish a new Redis connection
def connect_redis(host="localhost", port=6379, db=2):
    try:
        redis_db = redis.Redis(host=host, port=port, db=db)
        return redis_db
    except (ConnectionError, TimeoutError) as e:
        print(f"Error connecting to Redis: {e}")
        return None

# Function to define a new Oracle connection
def connect_oracle():
    try:
        # Read connection credentials from config file
        config = configparser.ConfigParser()
        config.read("config.ini")
        username = config.get("Oracle", "username")
        password = config.get("Oracle", "password")

        # Connect to Oracle using connection credentials
        oracle_db = cx_Oracle.connect(
            username,
            password,
            "localhost:1521/ORCL",
        )
        return oracle_db
    except cx_Oracle.Error as error:
        print("Error connecting to Oracle:", error)
        return None

# Function to establish a new MongoDB connection
def connect_mongodb():
    try:
        client = MongoClient('mongodb://localhost:27017/')
        mongodb = client['PortScanner']
        return mongodb
    except (ConnectionError, TimeoutError) as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

# Function to read the previous database choice from a file
def read_db_choice():
    try:
        with open('db_choice.yaml', 'r') as f:
            db_choice = f.readline().strip()
            if db_choice:
                print(f"Currently connected to '{db_choice}' database.")
                choice = input("Do you want to switch the database? (y/n) ")
                if choice.lower() == "y":
                    os.remove('db_choice.yaml')
                    return None
                else:
                    return db_choice
            else:
                return None
    except FileNotFoundError:
        # Create db_choice.yaml if it doesn't exist
        open('db_choice.yaml', 'w').close()
        return None
    except:
        return None


# Function to write the current database choice to a file
def write_db_choice(db_choice):
    try:
        with open('db_choice.yaml', 'w') as f:
            f.write(db_choice)
    except:
        pass


# Read the previous database choice
db_choice = read_db_choice()

# Connect to MySQL, Redis, Oracle, and MongoDB
mysql_db = None
redis_db = None
oracle_db = None
mongodb = None

if db_choice:
    # Attempt to connect to the database choice stored in the file
    if db_choice == "mysql":
        mysql_db = connect_mysql()
    elif db_choice == "redis":
        redis_db = connect_redis()
    elif db_choice == "oracle":
        oracle_db = connect_oracle()
    elif db_choice == "mongodb":
        mongodb = connect_mongodb()

else:
    # Prompt user for database choice if not stored in file
    while not db_choice:
        db_choice = input("Enter the database to write to (1 for MySQL, 2 for Redis, 3 for Oracle, 4 for MongoDB): ").strip().lower()
        if db_choice == "1":
            db_choice = "mysql"
            mysql_db = connect_mysql()
            if mysql_db is None:
                db_choice = None
        elif db_choice == "2":
            db_choice = "redis"
            redis_db = connect_redis()
            if redis_db is None:
                db_choice = None
        elif db_choice == "3":
            db_choice = "oracle"
            oracle_db = connect_oracle()
            if oracle_db is None:
                db_choice = None
        elif db_choice == "4":
            db_choice = "mongodb"
            mongodb = connect_mongodb()
            if mongodb is None:
                db_choice = None
        else:
            db_choice = None
        if not db_choice:
            print("Invalid database choice. Please try again.")

# Store the current database choice
write_db_choice(db_choice)

# Create a cursor object to interact with the MySQL database
mycursor = None

# Create a new database in MySQL
if db_choice == "mysql":
    mysql_db = connect_mysql()
    mycursor = mysql_db.cursor()
    mycursor.execute("CREATE DATABASE IF NOT EXISTS PortScanner")
    mycursor.execute("USE PortScanner")

    # Create table to store scan results in MySQL
    mycursor.execute(
        "CREATE TABLE IF NOT EXISTS ScanResults (id INT AUTO_INCREMENT PRIMARY KEY, destination VARCHAR(255), port_number INT, status VARCHAR(255)) ENGINE=InnoDB;")


# Create a new database table in Oracle
if db_choice == "oracle":
    oracle_db = connect_oracle()
    cursor = oracle_db.cursor()
    cursor.execute("""
    BEGIN
        EXECUTE IMMEDIATE 'CREATE TABLE ScanResults (
            id INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            destination VARCHAR2(255),
            port_number INT,
            status VARCHAR2(255)
        )';
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLCODE = -955 THEN
                NULL; -- Table already exists
            ELSE
                RAISE;
            END IF;
    END;
""")
    oracle_db.commit()
    cursor.close()

# Define lock for thread synchronization
object_lock = threading.Lock()

# Set default timeout for socket connections
socket.setdefaulttimeout(2)

# Prompt user for destination and resolve IP addresses
destinations = input("Enter the destinations: ").split(",")
hostIPs = []
for destination in destinations:
    hostIP = socket.gethostbyname(destination.strip())
    hostIPs.append(hostIP)
print("Scanning the host IP:", hostIPs)

# Define port scanning function
def portscanner(destination, hostIP, ports):
    soxx = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        connection = soxx.connect((hostIP, ports))
        with object_lock:
            print("The port", ports, "is currently open.")
        # Save scan result to the selected database
        if db_choice == "mysql":
            sql = "INSERT INTO ScanResults (destination, port_number, status) VALUES (%s, %s, %s)"
            val = (destination, ports, "open")
            mycursor.execute(sql, val)
            mysql_db.commit()
        elif db_choice == "redis":
            redis_db.rpush("ScanResults", {"destination": destination, "port_number": ports, "status": "open"})
        elif db_choice == "oracle":
            cursor = oracle_db.cursor()
            cursor.execute("INSERT INTO ScanResults (destination, port_number, status) VALUES (:destination, :port_number, :status)",
                           {"destination": destination, "port_number": ports, "status": "open"})
            oracle_db.commit()
            cursor.close()
        elif db_choice == "mongodb":
            collection = mongodb["ScanResults"]
            collection.insert_one({"destination": destination, "port_number": ports, "status": "open"})
    except:
        pass

# Create a queue to hold port numbers
port_queue = Queue()

# Populate the port queue
for ports in range(1, 1000):
    port_queue.put(ports)

# Function to scan ports
def scan_ports(destination, hostIP):
    while not port_queue.empty():
        ports = port_queue.get()
        portscanner(destination, hostIP, ports)
        port_queue.task_done()

# Create and start threads
for i in range(100):
    #2 imbeded for loops to be added 
    # outer for loop for the destination (which needs to go first)
    # inner for loop for the hosts 
    thread = threading.Thread(target=scan_ports, args=(destinations [1], hostIPs[0]))
    thread.daemon = True
    thread.start()

# Wait for all threads to complete
port_queue.join()

# Close the MySQL connection
if mysql_db:
    mysql_db.close()

# Close the Redis connection
if redis_db:
    redis_db.close()

# Close the Oracle connection
if oracle_db:
    oracle_db.close()

# Disconnect from MongoDB
if mongodb:
    mongodb.client.close()

print("Port scanning complete!")