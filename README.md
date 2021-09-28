Set of basic API tools for Cisco vManage written in Python 3

- Ensure you have the requirements installed:  pip install -r venv/requirements.txt
- Add your vManage address and credentials: edit includes.py
- Execute: python3 template.py

Currently has presents a menu with the following capabilities:

1. List Edges: lists all edges in inventory
2. RMA Device:
- prompts for a selection from a list of all devices in vManage Mode
- copies the template variables from, invalidates, and deletes that device
- prompts for a selection from a list of devices of the same device model in CLI Mode
- attaches template with the previous variables to the new device
3. Deploy Device
- prompts for a selection from a list of devices in CLI Mode
- prompts for a selection of templates that apply to that device model
- prompts for inputs for each template variable
- attaches template to the device
4. Change Device Values
- prompts for a selection from a list of devices in vManage Mode
- prompts for a selection from a list of variables for that device
- attaches template with changed variable
