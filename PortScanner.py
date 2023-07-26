#!/usr/bin/python3

import mysql.connector
import socket
import threading
from queue import Queue
from Configuration import my_host, my_port, my_user, my_password
import sys

###############################################################################

# Description:
# The Port Scanner is a Python script designed to scan the open ports of specified destinations. 
# It utilizes multiple database options, including MySQL, Redis, Oracle, and MongoDB, to store the scan results. 
# The script supports multithreading for efficient scanning.

###############################################################################

def main():
    # Create a queue to hold port numbers
    port_queue = Queue()

    # Populate the port queue (only first 50 for testing purposes)
    for ports in range(1, 50):
        port_queue.put(ports)

    # Connect to MySQL and create cursor
    mysql_db = connect_mysql()
    mycursor = None

    # Create a new database in MySQL
    mysql_db = connect_mysql()
    mycursor = mysql_db.cursor()
    mycursor.execute("CREATE DATABASE IF NOT EXISTS port_scanner")
    mycursor.execute("USE port_scanner")

    # Create table to store scan results in MySQL
    mycursor.execute("CREATE TABLE IF NOT EXISTS scan_results (id INT AUTO_INCREMENT PRIMARY KEY, destination VARCHAR(255), port_number INT, status VARCHAR(255)) ENGINE=InnoDB;")

    # Define lock for thread synchronization
    object_lock = threading.Lock()

    # Set default timeout for socket connections
    socket.setdefaulttimeout(2)

    # Prompt user for destination and resolve IP addresses
    if len(sys.argv) > 1:
        destinations = " ".join(sys.argv[1:]).split()
    else:
        destinations = input("Enter the destinations: ").split()

    for destination in destinations:
        hostIP = socket.gethostbyname(destination.strip())
        print("Scanning the host IP:", hostIP)
        for i in range(100):
            thread = threading.Thread(target=scan_ports, args=(destinations, port_queue, mycursor, object_lock, mysql_db))
            thread.daemon = True
            thread.start()

    # Wait for all threads to complete
    port_queue.join()

    if mysql_db:
        mysql_db.close()

    print("Port scanning complete!")

###############################################################################

# Function to create a new MySQL connection
def connect_mysql():
    try:
        mysql_db = mysql.connector.connect(host=my_host, port=my_port, user=my_user, password=my_password)
        return mysql_db
    except (mysql.connector.Error, ConnectionError, TimeoutError) as e:
        print(f"Error connecting to MySQL: {e}")
        return None

###############################################################################

# Define port scanning function
def port_scanner(destination, hostIP, ports, mycursor, object_lock, mysql_db):
    soxx = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        connection = soxx.connect((hostIP, ports))
        with object_lock:
            print("hostIP: ", hostIP, ", destination: ", destination, ", port: ", ports, " is open")
            sql = "INSERT INTO scan_results (destination, port_number, status) VALUES (%s, %s, %s)"
            val = (destination, ports, "open")
            mycursor.execute(sql, val)
            mysql_db.commit()
    except:
        pass

###############################################################################

# Function to scan ports
def scan_ports(destinations, port_queue, mycursor, object_lock, mysql_db):
    while not port_queue.empty():
        ports = port_queue.get()
        for destination in destinations:
            hostIP = socket.gethostbyname(destination.strip())
            port_scanner(destination, hostIP, ports, mycursor, object_lock, mysql_db)
        port_queue.task_done()

###############################################################################

if __name__ == "__main__":
    main()
