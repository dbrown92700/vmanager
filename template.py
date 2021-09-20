#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from vmanage_api import rest_api_lib
from includes import vmanage_name, vmanage_pass, vmanage_user
import json
from time import sleep

def list_device(vmanage):

    # Returns a list of all devices as dict {uuid, deviceModel}

    response = vmanage.get_request('device')
    num = 1
    deviceList = []
    for device in response['data']:
        print(f"{num:3}: {device['deviceId']:20}  {device['device-model']:20}")
        num += 1
        deviceList.append({'uuid': device['deviceId'], 'deviceModel': device['device-model']})
    return deviceList

def list_edges(vmanage, mode = 'all', model = 'all'):

    # Returns a list of Edges as dict {uuid, deviceModel}
    # Set mode to all, cli, or vmanage

    response = vmanage.get_request('system/device/vedge')
    num = 1
    deviceList = []
    for device in response['data']:
        if mode=='all' or device['configOperationMode']==mode:
            if model == 'all' or device['deviceModel'] == model:
                try:
                    hostname = device['host-name']
                except:
                    hostname = 'UNASSIGNED'
                print(f"{num:3}: {device['uuid']:50} {hostname:20} {device['deviceModel']:20}  {device['configOperationMode']:20}")
                num += 1
                deviceList.append({'uuid':device['uuid'],'deviceModel':device['deviceModel']})
    return deviceList

def rma_device(vmanage):

    # Perform RMA
    # - Download variables
    # - Invalidate and delete old device
    # - Attach template with variables to new device

    # General list of devices in vManage mode and prompt for replacement
    activeList = list_edges(vmanage, mode = 'vmanage')
    choice = input('Choose device to replace:')
    replaceThis = activeList[int(choice)-1]
    print(f'Replace Device Details:\n{replaceThis}')

    # Pull current template variables
    replaceVariables = get_device_template_variables(vmanage, deviceId=replaceThis['uuid'])
    print('\nDevice Variables:\n', json.dumps(replaceVariables, indent = 2))

    # Invalidate Device
    cert_status = set_certificate(vmanage, replaceThis['uuid'], replaceThis['deviceModel'], 'invalid')
    print(cert_status)

    # Delete old device
    delete_status = vmanage.delete_request(f'system/device/{replaceThis["uuid"]}')
    print(delete_status)


    # Generate list of devices of same model in CLI mode and prompt for replacement
    newList = list_edges(vmanage, mode = 'cli', model = replaceThis['deviceModel'])
    choice = input('Choose new device:')
    replaceWith = newList[int(choice)-1]
    print(replaceWith)

    # Create template variables JSON object with new UUID
    replaceVariables['device'][0]['csv-deviceId'] = replaceWith['uuid']
    payload = {"deviceTemplateList":[
        replaceVariables
    ]
    }
    print(json.dumps(payload,indent=2))

    attachment = vmanage.post_request('template/device/config/attachment', payload = payload)

    print(attachment)

def get_device_template_variables(vmanage, deviceId):

    response = vmanage.get_request(f'system/device/vedge?uuid={deviceId}')
    print(f"Device Template ID: {response['data'][0]['templateId']}")
    payload = {"templateId": f"{response['data'][0]['templateId']}", "deviceIds": [f"{deviceId}"], "isEdited": "false",
          "isMasterEdited": "false"}
    templateVariables = vmanage.post_request('template/device/config/input', payload)['data'][0]
    template = {
        "templateId": f"{response['data'][0]['templateId']}",
        "device": [
            templateVariables
        ],
        "isEdited": False,
        "isMasterEdited": False
    }
    return template

def get_device_template_form(vmanage, templateId):
    payload = {"templateId": f"{templateId}", "isEdited": "false",
            "isMasterEdited": "false"}
    templateVariables = vmanage.post_request('template/device/config/exportcsv', payload)

    return templateVariables

def set_certificate(vmanage, uuid, model, state):

    # Set device certificate state to valid, invalid or staging

    # Find existing certificate details for device UUID
    # Create certificate request payload JSON
    certrecords = vmanage.get_request(f'certificate/vedge/list?model={model}')['data']
    for device in certrecords:
        if device['uuid']==uuid:
            break
    payload = [
        {
        "serialNumber": f"{device['serialNumber']}",
        "chasisNumber": f"{uuid}",
        "validity": f"{state}"
        }
    ]

    cert_status = vmanage.post_request('certificate/save/vedge/list', payload)
    print("Set certificate state result:\n",json.dumps(cert_status, indent=2))

    cert_status = vmanage.post_request('certificate/vedge/list', payload='')
    print("Push certificate state to controllers result:\n",json.dumps(cert_status, indent=2))
    action_status(vmanage, cert_status['id'])

    return cert_status

def detach_edge(vmanage, deviceId, deviceIP):

    # Places Edge in CLI mode

    payload = {
        "deviceType":"vedge",
        "devices":[
            {
                "deviceId":f'{deviceId}',
                "deviceIP":f'{deviceIP}'
            }
        ]
    }
    response = vmanage.post_request('template/config/device/mode/cli', payload)
    print(response)
    return(response)

def action_status(vmanage, id):
    while (1):
        status_res = vmanage.get_request(f"device/action/status/{id}")['summary']
        print(status_res)
        if status_res['status'] == "done":
            if 'Success' in status_res['count']:
                return status_res
            elif 'Failure' in status_res['count']:
                return "Failed"
        sleep(5)

def change_device_values(vmanage):

    # Change a device value

    # Chose a device
    activeList = list_edges(vmanage, mode = 'vmanage')
    choice = input('Choose device to replace:')
    changeThis = activeList[int(choice)-1]
    print(f'Change values for:\n{json.dumps(changeThis, indent=2)}')

    # Get current values
    currentValues = get_device_template_variables(vmanage, changeThis['uuid'])
    print(f'Current values: \n{json.dumps(currentValues, indent=2)}')

    menulist = []
    menunum = 1
    for variable in currentValues['device'][0]:
        menu = '*'
        if variable[0] == '/':
            menu = str(menunum)
            menunum += 1
            menulist.append(variable)
        print(f'{menu:>2}: {variable:60} --- {currentValues["device"][0][f"{variable}"]}')
    choice = input('Which value do you want to change:')
    newvalue = input(f'Input new value for {menulist[int(choice) - 1]}: ')

    payload = {"deviceTemplateList":[
        currentValues
    ]
    }
    payload['deviceTemplateList'][0]['device'][0][menulist[int(choice) - 1]] = newvalue
    print(json.dumps(payload,indent=2))

    attachment = vmanage.post_request('template/device/config/attachment', payload = payload)

    print(attachment)

    action_status(vmanage, attachment['id'])

def deploy_device(vmanage):

    # Attach template to new device

    # Choose a device
    activeList = list_edges(vmanage, mode = 'cli')
    choice = input('Choose device to deploy:' )
    changeThis = activeList[int(choice)-1]
    print(f'Deploying:\n{json.dumps(changeThis, indent=2)}')

    # Choose a template
    menunum = 1
    menulist = []
    templateList = vmanage.get_request('template/device')['data']
    for template in templateList:
        if template['deviceType'] == changeThis['deviceModel']:
            menulist.append(template['templateId'])
            print(f'{menunum:2}: {template["templateName"]}')
            menunum += 1
    choice = int(input('Which template do you want to use:' )) - 1

    # Create input JSON
    payload = {
        "templateId": menulist[choice],
        "deviceIds":
            [
                changeThis['uuid']
            ],
        "isEdited": False,
        "isMasterEdited": False
    }
    templateInput = vmanage.post_request('template/device/config/input', payload=payload)['data'][0]

    print(json.dumps(templateInput, indent=2))

    print('Input new value or leave blank for (value):')
    for field in templateInput:
        if field[0] == '/':
            value = input(f'Enter {field} ({templateInput[field]}):') or templateInput[field]
            templateInput[field] = value
    payload = {
        "deviceTemplateList": [
            {
                "templateId": "86ec7ba3-aa21-4055-9271-9726c11da8ca",
                "device": [
                    templateInput
                    ],
                "isEdited": False,
                "isMasterEdited": False
            }
        ]
    }
    print(json.dumps(payload, indent=2))

    attachment = vmanage.post_request('template/device/config/attachment', payload = payload)
    print(attachment)
    action_status(vmanage, attachment['id'])

if __name__ == "__main__":

    vmanage = rest_api_lib(vmanage_name, vmanage_user, vmanage_pass)

    while True:
        user_funct = input("""
            1. List Edges
            2. RMA Device
            3. Deploy Device
            4. Change Device Values
            Which function do you want to do: """)

        if user_funct=='1':
            list_edges(vmanage)
        elif user_funct=='2':
            rma_device(vmanage)
        elif user_funct=='3':
            deploy_device(vmanage)
        elif user_funct=='4':
            change_device_values(vmanage)
        else:
            exit()
