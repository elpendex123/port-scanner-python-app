Vagrant.configure("2") do |config|
  # Choose the desired Alpine version
  config.vm.box = "generic/alpine312"

  config.vm.provider "virtualbox" do |vb|
    # Set the desired amount of memory in MB
    vb.memory = "512"

    # Set the number of CPUs
    vb.cpus = 1
  end

  # Use DHCP to assign a private IP address
  config.vm.network "private_network", type: "dhcp"  

  # Port forwarding for SSH
  config.vm.network "forwarded_port", guest: 22, host: 2222, id: "ssh"

  # Provisioning for the MySQL server (using MariaDB package)
  config.vm.provision "shell", inline: <<-SHELL
    # Update package list and install MariaDB (MySQL)
    apk update
    apk add mariadb mariadb-client

    # Initialize the MariaDB data directory and set appropriate permissions
    mysql_install_db --user=mysql --datadir=/var/lib/mysql
    chown -R mysql:mysql /var/lib/mysql

    # Start and enable MariaDB service
    rc-update add mariadb default
    service mariadb start

    # Secure MariaDB installation (optional, for development environments)
    # mysql_secure_installation

    # Optional: Additional configuration and setup can be added here
  SHELL
end