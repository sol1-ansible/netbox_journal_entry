#!/usr/bin/env python

__metaclass__ = type

DOCUMENTATION = r'''
---
module: netbox_journal_entry

short_description: Write to the Netbox Journal

description: Write Netbox Journal entries assigned to Netbox objects

options:
    netbox_url:
        description:
          - The URL of the NetBox instance.
          - Must be accessible by the Ansible control host.
        required: true
        type: str
    netbox_token:
        description: The NetBox API token.
        required: true
        type: str
    name:
        description: Name of the Netbox object to which the journal entry is assigned.
        required: true
        type: str
    type:
        description:
            - API type of the Netbox object to which the journal entry is assigned.
            - This may be "dcim.device" or "virtualization.virtualmachine".
        default: "dcim.device"
        required: false
        type: str
    comment:
        description: The comment annotating the journal entry
        required: true
        type: str

author:
    - "Oliver Lowe <o@olowe.co>"
'''

EXAMPLES = r'''
# Write a message to the journal for a Netbox device
- netbox_journal_entry:
    netbox_url: "https://netbox.example.com"
    netbox_token: "abcd1234"
    name: "mail.example.com"
    comment: "mail server configuration updated"
    state: present

# Write a journal entry that each virtual machine's system packages
# have been upgraded
- name: update packages
  package:
    name:
      - nginx
      - postfix
    state: latest

- name: log package update in netbox
  netbox_journal_entry:
    netbox_url: "https://netbox.example.com"
    netbox_token: "abcd1234"
    name: "{{ inventory_hostname }}"
    type: "virtualization.virtualmachine"
    comment: "system packages updated"
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
object_id:
    description: ID of the journal entry.
    type: int
    returned: always
    sample: 69
'''

import pynetbox
from ansible.module_utils.basic import AnsibleModule

def write_to_journal(netbox, comment, name, type="dcim.device", tags=[]):
    """
    Writes a journal entry consisting of comment for the named object
    with type type. type may be "virtualization.virtualmachine" or
    "dcim.device". netbox is an initialised pynetbox.api client.
    """
    endpoint = netbox.dcim.devices
    if type == "virtualization.virtualmachine":
        endpoint = netbox.virtualization.virtual_machines
    elif type != "dcim.device":
        raise ValueError("cannot create journal entry for %s" % type)

    obj = endpoint.get(name=name)
    if not obj:
        raise ValueError("no such object %s" % name)

    return netbox.extras.journal_entries.create(
        assigned_object_type=type,
        assigned_object_id=obj.id,
        comments=comment,
        tags=tags,
    )

def run_module():
    module_args = dict(
        name=dict(type="str", required=True),
        type=dict(type="str", required=False, default="dcim.device"),
        comment=dict(type="str", required=True),
        netbox_url=dict(type="str", required=True),
        netbox_token=dict(type="str", required=True),
        tags=dict(type="list", required=False, default=[]),
        state=dict(type="str", required=False, default="present"),
    )

    result = dict(
        changed=False,
        object_id=0,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        result["changed"] = True
        module.exit_json(**result)

    netbox = pynetbox.api(module.params["netbox_url"], token=module.params["netbox_token"])
    try:
        entry = write_to_journal(
            netbox,
            module.params["comment"],
            module.params["name"],
            module.params["type"],
            module.params["tags"],
        )
        result["changed"] = True
        result["id"] = entry.id
    except Exception as err:
        module.fail_json(msg=str(err), **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
