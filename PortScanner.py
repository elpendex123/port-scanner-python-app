import mysql.connector
import configparser
import socket
import threading
from queue import Queue
import uuid
import os

###############################################################################

# Description:
# The Port Scanner is a Python script designed to scan the open ports of specified destinations. 
# It utilizes multiple database options, including MySQL, Redis, Oracle, and MongoDB, to store the scan results. 
# The script supports multithreading for efficient scanning.

###############################################################################

# Function to create a new MySQL connection
def connect_mysql():
    try:
        host = "192.168.56.3"  
        port = 3306
        user = "mysql"
        password = "password"  

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

###############################################################################

# Function to establish a new MongoDB connection
def connect_mongodb():
    try:
        client = MongoClient('mongodb://localhost:27017/')
        mongodb = client['PortScanner']
        return mongodb
    except (ConnectionError, TimeoutError) as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

###############################################################################

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

###############################################################################

# Function to write the current database choice to a file
def write_db_choice(db_choice):
    try:
        with open('db_choice.yaml', 'w') as f:
            f.write(db_choice)
    except:
        pass

###############################################################################

# Connect to MySQL, Redis, Oracle, and MongoDB
mysql_db = None
db_choice = "mysql"
mysql_db = connect_mysql()

# Store the current database choice
write_db_choice(db_choice)

# Create a cursor object to interact with the MySQL database
mycursor = None

# Create a new database in MySQL
if db_choice == "mysql":
    mysql_db = connect_mysql()
    mycursor = mysql_db.cursor()
    mycursor.execute("CREATE DATABASE IF NOT EXISTS port_scanner")
    mycursor.execute("USE port_scanner")

    # Create table to store scan results in MySQL
    mycursor.execute(
        "CREATE TABLE IF NOT EXISTS scan_results (id INT AUTO_INCREMENT PRIMARY KEY, destination VARCHAR(255), port_number INT, status VARCHAR(255)) ENGINE=InnoDB;")

###############################################################################

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

###############################################################################

# Define port scanning function
def portscanner(destination, hostIP, ports):
    soxx = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        connection = soxx.connect((hostIP, ports))
        with object_lock:
            print("The port", ports, "is currently open.")
            sql = "INSERT INTO scan_results (destination, port_number, status) VALUES (%s, %s, %s)"
            val = (destination, ports, "open")
            mycursor.execute(sql, val)
            mysql_db.commit()
    except:
        pass

###############################################################################

# Create a queue to hold port numbers
port_queue = Queue()

# Populate the port queue
for ports in range(1, 1000):
    port_queue.put(ports)

###############################################################################

# Function to scan ports
def scan_ports(destination, hostIP):
    while not port_queue.empty():
        ports = port_queue.get()
        portscanner(destination, hostIP, ports)
        port_queue.task_done()

###############################################################################

# Create and start threads
for i in range(100):
    thread = threading.Thread(target=scan_ports, args=(destinations [0], hostIPs[0]))
    thread.daemon = True
    thread.start()

# Wait for all threads to complete
port_queue.join()

# Close the MySQL connection
if mysql_db:
    mysql_db.close()

print("Port scanning complete!")
