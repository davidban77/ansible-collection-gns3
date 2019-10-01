#!/usr/bin/env python

ANSIBLE_METADATA = {
    "metadata_version": "1.2",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: gns3_node_file
short_description: Updates/creates a file on a node directory
version_added: '2.8'
description:
    - "Updates/creates a file on a node directory of a GNS3 project"
requirements: [ gns3fy ]
author:
    - David Flores (@davidban77)
options:
    url:
        description:
            - URL target of the GNS3 server
        required: true
        type: str
    port:
        description:
            - TCP port to connect to server REST API
        type: int
        default: 3080
    user:
        description:
            - User to connect to GNS3 server
        type: str
    password:
        description:
            - Password to connect to GNS3 server
        type: str
    project_name:
        description:
            - Project name
        type: str
    project_id:
        description:
            - Project ID
        type: str
    node_name:
        description:
            - Node name
        type: str
    node_id:
        description:
            - Node ID
        type: str
    data:
        description:
            - The text to insert.
        type: str
    dest:
        description:
            - Node destination path. Like 'etc/network/interfaces'
        type: str
        required: true
    state:
        description:
            - If the file should present or absent
        type: str
        choices: ['present', 'absent']
        default: present
"""

EXAMPLES = """
# Retrieve the GNS3 server version
- name: Get the server version
  gns3_node_file:
    url: http://localhost
    port: 3080
    project_name: test_lab
    node_name: alpine-1
    data: |
        auto eth0
        iface eth0 inet dhcp
    dest: /etc/network/interfaces
"""
import traceback

GNS3FY_IMP_ERR = None
try:
    from gns3fy import Gns3Connector, Project

    HAS_GNS3FY = True
except ImportError:
    GNS3FY_IMP_ERR = traceback.format_exc()
    HAS_GNS3FY = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib


def node_write_file(module, node, path, data):
    "Writes text data into specified path of the node"
    try:
        node.write_file(path=path, data=data)
    except Exception as err:
        module.fail_json(msg=str(err), exception=traceback.format_exc())


def main():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(type="str", required=True),
            port=dict(type="int", default=3080),
            user=dict(type="str", default=None),
            password=dict(type="str", default=None, no_log=True),
            project_name=dict(type="str", default=None),
            project_id=dict(type="str", default=None),
            node_name=dict(type="str", default=None),
            node_id=dict(type="str", default=None),
            data=dict(type="str", default=None),
            dest=dict(type="str", required=True),
            state=dict(type="str", choices=["present", "absent"], default="present"),
        ),
        required_one_of=[["project_name", "project_id"], ["node_name", "node_id"]],
    )
    if not HAS_GNS3FY:
        module.fail_json(msg=missing_required_lib("gns3fy"), exception=GNS3FY_IMP_ERR)
    result = dict(changed=False)

    server_url = module.params["url"]
    server_port = module.params["port"]
    server_user = module.params["user"]
    server_password = module.params["password"]
    project_name = module.params["project_name"]
    project_id = module.params["project_id"]
    node_name = module.params["node_name"]
    node_id = module.params["node_id"]
    data = module.params["data"]
    dest = module.params["dest"]
    state = module.params["state"]
    if state == "present" and data is None:
        module.fail_json(msg="Parameter needs to be passed: data", **result)

    # Create server session
    server = Gns3Connector(
        url=f"{server_url}:{server_port}", user=server_user, cred=server_password
    )
    # Define the project
    if project_name is not None:
        project = Project(name=project_name, connector=server)
    elif project_id is not None:
        project = Project(project_id=project_id, connector=server)
    if project is None:
        module.fail_json(msg="Could not retrieve project. Check name", **result)

    # Retrieve project info
    project.get()

    # Define the Node
    if node_name is not None:
        node = project.get_node(name=node_name)
    elif node_id is not None:
        node = project.get_node(node_id=node_id)
    if node is None:
        module.fail_json(msg="Could not retrieve node. Check name", **result)

    # Try to get file data
    try:
        file_data = node.get_file(path=dest)
    except Exception as err:
        if "not found" in str(err):
            file_data = None
        else:
            module.fail_json(msg=str(err), exception=traceback.format_exc())

    if state == "absent":
        if file_data is None or file_data == "":
            result.update(changed=False)
        else:
            # Delete node file data
            # As of now (GNS3 v2.2.rc5) the DELETE method is not allowed
            node_write_file(module, node, dest, "")
            result.update(changed=True)
    elif state == "present":
        if file_data == data:
            result.update(changed=False)
        else:
            node_write_file(module, node, dest, data)
            result.update(changed=True)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
