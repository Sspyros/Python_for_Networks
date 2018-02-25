import paramiko
import os.path
import subprocess
import time
import sys
import re
import os
import ipaddress
import socket
import networkx
import matplotlib.pyplot as mtplot

FNULL = open(os.devnull, 'w')

#Check password file validity
def pass_is_valid():
	global pass_dictionary
	pass_dictionary = []
	while True:
		print '*Choose passwords file:'
		print '1. Use password.txt in current directory'
		print '2. Choose different file'
		user_input = raw_input('\n# Type 1 or 2: ')
		if user_input == '2' : pass_file = raw_input("\n# Enter pass file name and extension: ")
		elif user_input == '1': pass_file = 'password.txt'
		else:
			print '\n* INVALID option! Please try again.\n'
			continue
		if os.path.isfile(pass_file) == True:
			print "\n* Password file has been validated.\n"
			break

		else:
			print "\n* File %s does not exist! Please check and try again!\n" % pass_file
			continue
	open_pass_file = open(pass_file, 'r')

#Create dictionary with all passwords from file
	for line in open_pass_file: pass_dictionary.append(line.strip('\n'))
#Remove blank passwords
	pass_dictionary = filter(None, pass_dictionary)
#Remove diplicate entries
	pass_dictionary = list(set(pass_dictionary))
	open_pass_file.close()
		
#Check IP range file validity
def ip_is_valid():
	check = False
	global valid_ip
	global blacklist
	network_list = []
	valid_ip = []
	blacklist = []
	while True:
		print '* Choose IP networks file:'
		print '1. Use range.txt in current directory.'
		print '2. Choose different file.'
		user_input = raw_input('\n# Type 1 or 2: ')
		
		if user_input == '2' : range_file = raw_input("\n# Enter pass file name and extension: ")
		elif user_input == '1': range_file = 'range.txt'
		else:
			print '\n* INVALID option! Please try again.\n'
			continue
			
		if os.path.isfile(range_file) == True: print "\n* Password file has been validated.\n"
		else:
			print "\n* File %s does not exist! Please check and try again!\n" % range_file
			continue

	#Checking octets
		o_range_file = open(range_file, 'r')
		o_range_file.seek(0)
		for line in o_range_file:
			network_list.extend(line.strip('\n').split(','))
		check = True
		
	#Check reachable IP addresses
		for network in network_list:
			try:
				a = list(ipaddress.ip_network(network).hosts())
				for ip in a:
					try:
						ping_reply = subprocess.check_call(['ping', '-c', '2', '-w', '2', '-q', '-n', str(ip)],stdout=FNULL, stderr=FNULL )
					except subprocess.CalledProcessError:
						ping_reply = None
					if ping_reply is 0:
						valid_ip.append(str(ipaddress.IPv4Address(ip)))
			except ValueError:
				print '\n* There was an INVALID IP address! Please check and try again!\n'
				check = False
				break

	#Evaluating the 'check' flag
		if check == False:
			continue
		check = True
		if check == True:
			o_range_file.close()
			break

#Check correct passwords for valid IP addresses
def check_ssh_conn(ip, code = 0):
	for passw in pass_dictionary:
		try:
			session = paramiko.SSHClient()
			session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			session.connect(ip, username = 'admin', password = passw)
			connection = session.invoke_shell()
		except paramiko.AuthenticationException:
			code = 1		
		except socket.error as e:
			code = 2
			blacklist.append(ip)
		session.close()
		if code == 0: correct_passwords[ip] = passw

#Create SSH connection, send commands and extract necessary information
def open_ssh_con(ip, i):
	try:         
		session = paramiko.SSHClient()
		session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		session.connect(ip, username = 'admin', password = correct_passwords[ip])
		connection = session.invoke_shell()
		connection.send('terminal length 0\n')
		time.sleep(1)
		connection.send('\n')
		connection.send('show inventory\n')
		time.sleep(2)
		connection.send('show hardware | begin processor\n')
		time.sleep(1)
		connection.send('show hardware | include Software\n')
		time.sleep(1)
		connection.send('show interface description\n')
		time.sleep(1)
		connection.send('show cdp neighbor\n')
		time.sleep(1)
		router_output = connection.recv(65535)
		devices['device' + str(i)]['name'] = re.search('(.+)#',router_output).group(1)
		devices['device' + str(i)]['hw_info'] = re.search('((.*\n){3})\d+\s\w+', router_output).group(1).strip('\r')
		devices['device' + str(i)]['sw_info'] = re.search('Software\r\n(.*)', router_output).group(1).strip('\r')
		devices['device' + str(i)]['password'] = correct_passwords[ip]
		devices['device' + str(i)]['modules'] = re.findall('(NAME.*\r\nPID.*)', router_output)
		devices['device' + str(i)]['ports'] = re.search('description\r\n((.*\n)+?).*#', router_output).group(1).replace(devices['device' + str(i)]['name'] + '#','')
		neighbor = re.search('ID\r\n((.*\n)+)', router_output).group(1)
		devices['device' + str(i)]['neighbors'] = [devices['device' + str(i)]['name'], list(re.findall('(.*)\.', neighbor))]

	except paramiko.AuthenticationException:
		print '** Authentication Error sending the commands **'

	session.close()
								
def create_output_txt():
	print '* Choose output directory:'
	user_input = raw_input('1. Create output.txt in current folder.\n2. Choose destination name.\n\n# Type 1 or 2: ')
	if user_input is '1': output_file = open('output.txt', 'w')
	elif user_input is '2':
		dst = raw_input('\n# Enter destination name: ') 
		output_file = open(dst, 'w')
	else:
		print '\n INVALID option. Please try again.'
		return 1
	
	for dev in devices:
		output_file.write('* Device Name: ' +  devices[dev]['name'] + '\n')
		output_file.write('\n* Device IP: '+  devices['device' + str(i)]['mgmt_ip'] + '\n')
		output_file.write('\n* Device Password: ' +  devices['device' + str(i)]['password'] + '\n')
		output_file.write('\n* Hardware Info: \n' + devices['device' + str(i)]['hw_info']  + '\n')
		output_file.write('* Software Info: \n' + devices['device' + str(i)]['sw_info'] + '\n')
		output_file.write('\n* Modules: \n' + '\n'.join(devices['device' + str(i)]['modules']) + '\n')
		output_file.write('\n* Ports: \n' + devices['device' + str(i)]['ports'] + '\n')
		output_file.write('===================================================================\n\n')
	output_file.close()
	print('\n* Info for all devices printed to text file.\n')
	return 0
	
def print_output():
	print '* Choose option:'
	user_input = raw_input('-Type exit to skip displaying info and proceed to create topology graph.\n-Type list to list all devices\n-Type device name to print all info about the device\n\n#')
	if user_input == 'exit': return 0
	if user_input == 'list': 
		for dev in devices: 
			print('\nDevice: ' + devices[dev]['name'] + ' with IP: ' + devices[dev]['mgmt_ip']) 
	else:
		for dev in devices:
			if devices[dev]['name'] == user_input:
				print '\n* Device Name: ' +  devices[dev]['name'] + '\n'
				print '* Device IP: '+  devices[dev]['mgmt_ip'] + '\n'
				print '* Device Password: ' +  devices[dev]['password'] + '\n'
				print '* Hardware Info: \n' + devices[dev]['hw_info']  + '\n'
				print '* Software Info: \n' + devices[dev]['sw_info'] + '\n'
				print '* Modules: \n' + '\n'.join(devices[dev]['modules']) + '\n'
				print '* Ports: \n' + devices[dev]['ports'] + '\n'
	return 1

def create_topology():
	print '\n* Creating topology image.\n'
	graph = networkx.Graph()
	neighborship={}

	for router in neighbour:
		for second_router in neighbour:
			if second_router==router:
				continue
			if router[0] in second_router[1]:
				graph.add_edge(router[0],second_router[0])

	graph.add_edges_from(neighborship.keys())
	pos = networkx.spring_layout(graph, k = 0.1, iterations = 70)
	networkx.draw_networkx_labels(graph, pos, font_size = 9, font_family = "sans-serif", font_weight = "bold")
	networkx.draw_networkx_edges(graph, pos, width = 4, alpha = 0.4, edge_color = 'black')
	networkx.draw_networkx_edge_labels(graph, pos, neighborship, label_pos = 0.3, font_size = 6)
	networkx.draw(graph, pos, node_size = 800, with_labels = False, node_color = 'b')
	mtplot.savefig('topology.png')
	#mtplot.show()

#Calling user file validity function    
try:
  pass_is_valid()
    
except KeyboardInterrupt:
	print "\n\n* Program aborted by user. Exiting...\n"
	sys.exit()

#Calling IP validity function    
try:
	ip_is_valid()
    
except KeyboardInterrupt:
	print "\n\n* Program aborted by user. Exiting...\n"
	sys.exit()
		
correct_passwords = {}
print '* Trying passwords from dictionary for reachable IP addresses.\n'
for ip in valid_ip:
	try:
		check_ssh_conn(ip)
	
	except KeyboardInterrupt:
		print "\n\n* Program aborted by user. Exiting...\n"
		sys.exit()

#Remove valid IP addresses if SSH fails (removes host PCs)
devices = {}
for ip in blacklist:
	if ip in valid_ip: valid_ip.remove(ip)

#Create dictionary with the information for every device
print '* Opening SSH connection and sending commands for each device.\n'
neighbour = []
for i, ip in enumerate(valid_ip):
	devices.update({'device'+str(i):{'name':'', 'mgmt_ip':ip,'password':'','hw_info':'','sw_info':'','modules':'','ports':'', 'neighbors':''}})
	try:
		open_ssh_con(ip, i)
	except KeyboardInterrupt:
		print "\n\n* Program aborted by user. Exiting...\n"
		sys.exit()

	neighbour.append(devices['device' + str(i)]['neighbors'])

#Create output .txt file with the information for all devices
try:
	while  create_output_txt(): print''
except KeyboardInterrupt:
	print "\n\n* Program aborted by user. Exiting...\n"
	sys.exit()

#Prompt user to print information for specific device	
try:
	while print_output(): print ''
except KeyboardInterrupt:
	print "\n\n* Program aborted by user. Exiting...\n"
	sys.exit()

#Create image of network topology
try:
	create_topology()
except KeyboardInterrupt:
	print "\n\n* Program aborted by user. Exiting...\n"
	sys.exit()

