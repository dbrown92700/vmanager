
"""
Class with REST Api GET and POST libraries

Updated for vManage 19.2 to include Cross Site Scripting Token

Example: python rest_api_lib.py vmanage_hostname username password

PARAMETERS:
	vmanage_hostname : Ip address of the vmanage or the dns name of the vmanage
	username : Username to login the vmanage
	password : Password to login the vmanage

Note: All the three arguments are manadatory
"""
import requests
import sys
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class rest_api_lib:
	def __init__(self, vmanage_ip, username, password):
		self.vmanage_ip = vmanage_ip
		self.session = {}
		self.login(self.vmanage_ip, username, password)
		self.token = self.get_request('client/token')

	def login(self, vmanage_ip, username, password):
		"""Login to vmanage"""
		base_url_str = 'https://%s/'%vmanage_ip

		login_action = '/j_security_check'

		#Format data for loginForm
		login_data = {'j_username' : username, 'j_password' : password}

		#Url for posting login data
		login_url = base_url_str + login_action

		url = base_url_str + login_url

		sess = requests.session()

		#If the vmanage has a certificate signed by a trusted authority change verify to True
		login_response = sess.post(url=login_url, data=login_data, verify=False)
		
		#print(login_response.content)

		#if '<html>' in login_response.content:
		#	print("Login Failed")
		#	sys.exit(0)

		self.session[vmanage_ip] = sess

	def get_request(self, mount_point, headers={'Content-Type': 'application/json'}, params=''):
		"""GET request"""
		url = "https://%s:8443/dataservice/%s"%(self.vmanage_ip, mount_point)
		#print (url)
		#print (headers)
		#print (params)
		response = self.session[self.vmanage_ip].get(url, headers=headers, params=params, verify=False)
		# print(response)
		data = response.content.decode('utf-8')
		try:
			data = json.loads(data)
		except:
			pass
		return data

	def post_request(self, mount_point, payload, headers={'Content-Type': 'application/json'}):
		"""POST request"""
		url = "https://%s:8443/dataservice/%s"%(self.vmanage_ip, mount_point)
		payload = json.dumps(payload)
		headers['X-XSRF-TOKEN']=self.token
		response = self.session[self.vmanage_ip].post(url=url, data=payload, headers=headers, verify=False)
		data = json.loads(response.content)
		return data

	def delete_request(self, mount_point):
		"""DELETE request"""
		url = "https://%s:8443/dataservice/%s"%(self.vmanage_ip, mount_point)
		response = self.session[self.vmanage_ip].delete(url=url, verify=False)
		data = json.loads(response.content)
		return data
'''
Sample Calls:

List Devices
	devices = obj.get_request('device')
List Device Templates
	templates = obj.get_request('template/device')
List Devices Attached to Template
	attached = obj.get_request(f'template/device/config/attached/{templateId}')
Create Device Input Variables
	payload = {"templateId":f"{templateId}","deviceIds":[f"{deviceId}"],"isEdited":"false","isMasterEdited":"false"}
	variables = obj.post_request('template/device/config/input', payload)

'''

		
def main(args):
	if not len(args) == 3:
		print (__doc__)
		return
	vmanage_ip, username, password = args[0], args[1], args[2]
	obj = rest_api_lib(vmanage_ip, username, password)
	#Example request to get devices from the vmanage "url=https://vmanage.viptela.com/dataservice/device"
	response = obj.get_request('device')
	print (response)
	#Example request to make a Post call to the vmanage "url=https://vmanage.viptela.com/dataservice/device/action/rediscover"
	payload = {"action":"rediscover","devices":[{"deviceIP":"172.16.248.105"},{"deviceIP":"172.16.248.106"}]}
	response = obj.post_request('device/action/rediscover', payload)
	print (response)

if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))