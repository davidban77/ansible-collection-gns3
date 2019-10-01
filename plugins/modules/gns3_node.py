#!/usr/bin/env python

ANSIBLE_METADATA = {
    "metadata_version": "1.2",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: gns3_node
short_description: Module to operate a node in a GNS3 server project
version_added: '2.8'
description:
    - Module to operate a node in a GNS3 server project.
    - It starts/stops/suspend/reloads a node.
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
    state:
        description:
            - State of the node, it can be:
            - '- C(started): Starts a node'
            - '- C(stopped): Stops a node'
            - '- C(suspended): Suspends a node'
            - '- C(reload): Special non-idempotent action that reloads a node'
        type: str
        choices: ['started', 'stopped', 'suspended', 'reload']
    retry:
        description:
            - Retries an action based on the state, if true and state is set to reload
            - it will reload the device and try to start it again if the status was not
            - changed
        type: bool
        default: false
    poll_wait_time:
        description:
            - Delay in seconds to wait to poll nodes when they are started/stopped.
            - Used when I(nodes_state) is C(started)/C(stopped)
        type: int
        default: 5
    force_project_open:
        description:
            - It will open the project (if closed) to interact with the device.
            - Otherwise it will throw out an error
        type: bool
        default: false
"""

EXAMPLES = """
# Open a GNS3 project and start router01 node
- name: Start node
  gns3_node:
    url: http://localhost
    project_name: lab_example
    node_name: router01
    node_state: started
    force_project_open: true

# Stop a node and wait 10 seconds to poll for status
- name: Stop node
  gns3_node:
    url: http://localhost
    project_name: lab_example
    node_name: router01
    state: stopped

# Suspend a node based on UUID
- name: Suspend node
  gns3_node:
    url: http://localhost
    project_name: lab_example
    node_id: 'ROUTER-UUID-SOMETHING-1234567'
    state: suspended

# Reload a node and apply a retry to start if needed
- name: Stop lab
  gns3_node:
    url: http://localhost
    project_id: 'PROJECT-UUID-SOMETHING-1234567'
    node_name: router01
    state: reload
    retry: true
    poll_wait_time: 30
"""

RETURN = """
name:
    description: Project name
    type: str
project_id:
    description: Project UUID
    type: str
node_id:
    description: Node UUID
    type: str
status:
    description: Project status. Possible values: opened, closed
    type: str
node_directory:
    description: Path of the node on the server (works only with compute=local)
    type: str
node_type:
    description: Network node type
    type: str
"""
import time
import traceback
from ansible.module_utils.basic import AnsibleModule, missing_required_lib

GNS3FY_IMP_ERR = None
try:
    from gns3fy import Gns3Connector, Project

    HAS_GNS3FY = True
except Exception:
    HAS_GNS3FY = False
    GNS3FY_IMP_ERR = traceback.format_exc()


def return_node_data(node):
    "Returns the node main attributes"
    return dict(
        name=node.name,
        project_id=node.project_id,
        node_id=node.node_id,
        status=node.status,
        node_directory=node.node_directory,
        node_type=node.node_type,
    )


def state_verification(expected_state, node, retry=False, poll_wait_time=5):
    "Verifies node state and returns a changed attribute"
    if expected_state == "started" and node.status != "started":
        node.start()
        if node.status != "started" and retry:
            node.start()
        return True
    elif expected_state == "stopped" and node.status != "stopped":
        node.stop()
        if node.status != "stopped" and retry:
            node.stop()
        return True
    elif expected_state == "suspended" and node.status != "suspended":
        node.suspend()
        if node.status != "suspended" and retry:
            node.suspend()
        return True
    elif expected_state == "reload":
        node.reload()
        time.sleep(poll_wait_time)
        node.get()
        if node.status != "started" and retry:
            node.start()
        return True
    return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(type="str", required=True),
            port=dict(type="int", default=3080),
            user=dict(type="str", default=None),
            password=dict(type="str", default=None, no_log=True),
            state=dict(
                type="str",
                required=True,
                choices=["started", "stopped", "suspended", "reload"],
            ),
            project_name=dict(type="str", default=None),
            project_id=dict(type="str", default=None),
            node_name=dict(type="str", default=None),
            node_id=dict(type="str", default=None),
            retry=dict(type="bool", default=False),
            poll_wait_time=dict(type="int", default=5),
            force_project_open=dict(type="bool", default=False),
        ),
        required_one_of=[["project_name", "project_id"], ["node_name", "node_id"]],
    )
    result = dict(changed=False)
    if not HAS_GNS3FY:
        module.fail_json(msg=missing_required_lib("gns3fy"), exception=GNS3FY_IMP_ERR)

    server_url = module.params["url"]
    server_port = module.params["port"]
    server_user = module.params["user"]
    server_password = module.params["password"]
    state = module.params["state"]
    project_name = module.params["project_name"]
    project_id = module.params["project_id"]
    node_name = module.params["node_name"]
    node_id = module.params["node_id"]
    retry = module.params["retry"]
    poll_wait_time = module.params["poll_wait_time"]
    force_project_open = module.params["force_project_open"]

    try:
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

        project.get()
        if project.status != "opened" and force_project_open:
            project.open()

        # Retrieve node
        if node_name is not None:
            node = project.get_node(name=node_name)
        elif node_id is not None:
            node = project.get_node(node_id=node_id)
        if node is None:
            module.fail_json(msg="Could not retrieve node. Check name", **result)
    except Exception as err:
        module.fail_json(msg=str(err), **result)

    # Apply state change
    result["changed"] = state_verification(
        expected_state=state, node=node, retry=retry, poll_wait_time=poll_wait_time
    )

    # Return the node data
    result["node"] = return_node_data(node)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
