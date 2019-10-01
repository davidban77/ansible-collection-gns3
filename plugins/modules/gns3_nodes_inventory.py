#!/usr/bin/env python

ANSIBLE_METADATA = {
    "metadata_version": "1.2",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: gns3_nodes_inventory
short_description: Retrieves GNS3 a project nodes console information
version_added: '2.8'
description:
    - "Retrieves nodes inventory information from a GNS3 project"
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
"""

EXAMPLES = """
# Retrieve the GNS3 server version
- name: Get the server version
  gns3_nodes_inventory:
    url: http://localhost
    port: 3080
    project_name: test_lab
  register: nodes_inventory

- debug: var=nodes_inventory
"""

RETURN = """
nodes_inventory:
    description: Dictionary that contain: name, server, console_port, console_type,
    type and template of each node
    type: dict
total_nodes:
    description: Total number of nodes
    type: int
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


def main():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(type="str", required=True),
            port=dict(type="int", default=3080),
            user=dict(type="str", default=None),
            password=dict(type="str", default=None, no_log=True),
            project_name=dict(type="str", default=None),
            project_id=dict(type="str", default=None),
        ),
        required_one_of=[["project_name", "project_id"]],
    )
    if not HAS_GNS3FY:
        module.fail_json(msg=missing_required_lib("gns3fy"), exception=GNS3FY_IMP_ERR)
    result = dict(changed=False, nodes_inventory=None, total_nodes=None)

    server_url = module.params["url"]
    server_port = module.params["port"]
    server_user = module.params["user"]
    server_password = module.params["password"]
    project_name = module.params["project_name"]
    project_id = module.params["project_id"]

    # Create server session
    server = Gns3Connector(
        url=f"{server_url}:{server_port}", user=server_user, cred=server_password
    )
    # Define the project
    if project_name is not None:
        project = Project(name=project_name, connector=server)
    elif project_id is not None:
        project = Project(project_id=project_id, connector=server)

    # Retrieve project info
    project.get()

    nodes_inventory = project.nodes_inventory()
    result.update(
        nodes_inventory=nodes_inventory, total_nodes=len(nodes_inventory.keys())
    )

    module.exit_json(**result)


if __name__ == "__main__":
    main()
