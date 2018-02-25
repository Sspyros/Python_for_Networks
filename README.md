# Python_for_Networks

Project by _Spyridon Spyriadis_ and _Uggen Dhanabalan_

**Description:**
This a network discovery program, it is designed to provide basic details about all devices within network. The program uses SSH to gather information about all available devices in the network and creates a text file as well as an image of the topology.

**Functionality:**
1. Show device(router) information
     - Hardware information
     - OS version
     - Management IP address
     - password
     - Installed modules
2. Show port status and it’s description 
3. Show topology of the network  

**Execution:** 
To run this program, Python 2.7 and the following libraries are required for the program to be executed:
* [Networkx](https://pypi.python.org/pypi/networkx/2.1)
* [Matplotlib](https://matplotlib.org/users/installing.html)
* [paramiko](https://pypi.python.org/pypi/paramiko/2.2.1)

To execute the file, type `python network_discovery.py` in Python shell. The user will be prompted to select the files containing the network IP ranges and the passwords for the SSH connection. After gathering all the necessary information, the user is prompted to decide where to save the output text file.
