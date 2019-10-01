#!/usr/bin/env python

ANSIBLE_METADATA = {
    "metadata_version": "1.4",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: gns3_project
short_description: Module to interact with GNS3 server projects
version_added: '2.8'
description:
    - 'Module to interact with GNS3 server projects.
    - It is using the L(gns3fy library,https://davidban77.github.io/gns3fy/)'
    - It opens/closes projects and performs basic turnup/teradown operations on nodes.
    - It creates/updates or deletes projects.
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
    state:
        description:
            - State of the project to be on the GNS3 server
            - '- C(opened): Opens a project and turns up nodes'
            - '- C(closed): Closes a project and turns down nodes'
            - '- C(present): Creates/update a project on the server'
            - '- C(absent): Deletes a project on the server'
        type: str
        choices: ['opened', 'closed', 'present', 'absent']
    project_name:
        description:
            - Project name
        type: str
    project_id:
        description:
            - Project ID
        type: str
    nodes_state:
        description:
            - Starts/stops nodes on the project.
            - Used when I(state) is C(opened)/C(closed)
        type: str
        choices: ['started', 'stopped']
    nodes_strategy:
        description:
            - Start/stop strategy of the devices defined on the project.
            - '- C(all): It starts/stops all nodes at once'
            - '- C(one_by_one): It starts/stops nodes serialy using I(nodes_delay) time
            between each action'
            - Used when I(state) is C(opened)/C(closed)
        type: str
        choices: ['all', 'one_by_one']
        default: 'all'
    nodes_delay:
        description:
            - Delay time in seconds to wait between nodes start/stop
            - Used when I(nodes_strategy) is C(one_by_one)
        type: int
        default: 10
    poll_wait_time:
        description:
            - Delay in seconds to wait to poll nodes when they are started/stopped.
            - Used when I(nodes_state) is C(started)/C(stopped)
        type: int
        default: 5
    nodes_spec:
        description:
            - List of dictionaries specifying the nodes properties.
            - '- Mandatory attributes: C(name), C(node_type) and C(template).'
            - '- Optional attributes: C(compute_id). It defaults to C(local)'
        type: list
    links_spec:
        description:
            - 'List of lists specifying the links endpoints. Example: C(- ["alpine-1",
            "eth0", "alpine-2", "eth0"])'
            - 'Mandatory attributes: C(node_a), C(port_a), C(node_b) and C(port_b)'
        type: list
"""

EXAMPLES = """
# Open a GNS3 project
- name: Start lab
  gns3_project:
    url: http://localhost
    state: opened
    project_name: lab_example

# Stop all nodes inside an open project
- name: Stop nodes
  gns3_project:
    url: http://localhost
    state: opened
    project_name: lab_example
    nodes_state: stopped
    nodes_strategy: all
    poll_wait_time: 5

# Open a GNS3 project and start nodes one by one with a delay of 10sec between them
- name: Start nodes one by one
  gns3_project:
    url: http://localhost
    state: opened
    project_name: lab_example
    nodes_state: started
    nodes_strategy: one_by_one
    nodes_delay: 10

# Close a GNS3 project
- name: Stop lab
  gns3_project:
    url: http://localhost
    state: closed
    project_id: 'UUID-SOMETHING-1234567'

# Create a GNS3 project
- name: Create a project given nodes and links specs
  gns3_project:
    url: http://localhost
    state: present
    project_name: new_lab
    nodes_spec:
        - name: alpine-1
          node_type: docker
          template: alpine
        - name: alpine-2
          node_type: docker
          template: alpine
    links_spec:
        - ('alpine-1', 'eth0', 'alpine-2', 'eth1')

# Delete a GNS3 project
- name: Delete project
  gns3_project:
    url: http://localhost
    state: absent
    project_name: new_lab
"""

RETURN = """
name:
    description: Project name
    type: str
project_id:
    description: Project UUID
    type: str
status:
    description: Project status. Possible values: opened, closed
    type: str
path:
    description: Path of the project on the server (works only with compute=local)
    type: str
auto_close:
    description: Project auto close when client cut off the notifications feed
    type: bool
auto_open:
    description: Project open when GNS3 start
    type: bool
auto_start:
    description: Project start when opened
    type: bool
filename:
    description: Project filename
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


def return_project_data(project):
    "Returns the project main attributes"
    return dict(
        name=project.name,
        project_id=project.project_id,
        status=project.status,
        path=project.path,
        auto_close=project.auto_close,
        auto_open=project.auto_open,
        auto_start=project.auto_start,
        filename=project.filename,
    )


# def nodes_state_verification(module, project, result):
def nodes_state_verification(
    expected_nodes_state, nodes_strategy, nodes_delay, poll_wait_time, project
):
    "Verifies each node state and returns a changed attribute"
    nodes_statuses = [node.status for node in project.nodes]

    # Verify if nodes do not match expected state
    if expected_nodes_state == "started" and any(
        status == "stopped" for status in nodes_statuses
    ):
        # Turnup the nodes based on strategy
        if nodes_strategy == "all":
            project.start_nodes(poll_wait_time=poll_wait_time)
        elif nodes_strategy == "one_by_one":
            for node in project.nodes:
                if node.status != "started":
                    node.start()
                    time.sleep(nodes_delay)
        return True
    elif expected_nodes_state == "stopped" and any(
        status == "started" for status in nodes_statuses
    ):
        # Shutdown nodes based on strategy
        if nodes_strategy == "all":
            project.stop_nodes(poll_wait_time=poll_wait_time)
        elif nodes_strategy == "one_by_one":
            for node in project.nodes:
                if node.status != "stopped":
                    node.stop()
                    time.sleep(nodes_delay)
        return True
    return False


def create_node(node_spec, project, module):
    "Creates the node specified in nodes_spec"
    # If exceptions occur then print them out in ansible format
    try:
        project.create_node(**node_spec)
    except Exception as err:
        module.fail_json(msg=str(err), exception=traceback.format_exc())


def create_link(link_spec, project, module):
    "Creates the node specified in nodes_spec"
    # If exceptions occur then print them out in ansible format
    try:
        project.create_link(*link_spec)
    except ValueError as err:
        if "At least one port is used" in str(err):
            return False
        else:
            module.fail_json(msg=str(err), exception=traceback.format_exc())
    except Exception as err:
        module.fail_json(msg=str(err), exception=traceback.format_exc())
    return True


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
                choices=["opened", "closed", "present", "absent"],
            ),
            project_name=dict(type="str", default=None),
            project_id=dict(type="str", default=None),
            nodes_state=dict(type="str", choices=["started", "stopped"]),
            nodes_strategy=dict(
                type="str", choices=["all", "one_by_one"], default="all"
            ),
            nodes_delay=dict(type="int", default=10),
            poll_wait_time=dict(type="int", default=5),
            nodes_spec=dict(type="list"),
            links_spec=dict(type="list"),
        ),
        supports_check_mode=True,
        required_one_of=[["project_name", "project_id"]],
        required_if=[["nodes_strategy", "one_by_one", ["nodes_delay"]]],
    )
    result = dict(changed=False)
    if not HAS_GNS3FY:
        module.fail_json(msg=missing_required_lib("gns3fy"), exception=GNS3FY_IMP_ERR)
    if module.check_mode:
        module.exit_json(**result)

    server_url = module.params["url"]
    server_port = module.params["port"]
    server_user = module.params["user"]
    server_password = module.params["password"]
    state = module.params["state"]
    project_name = module.params["project_name"]
    project_id = module.params["project_id"]
    nodes_state = module.params["nodes_state"]
    nodes_strategy = module.params["nodes_strategy"]
    nodes_delay = module.params["nodes_delay"]
    poll_wait_time = module.params["poll_wait_time"]
    nodes_spec = module.params["nodes_spec"]
    links_spec = module.params["links_spec"]

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
    except Exception as err:
        module.fail_json(msg=str(err), **result)

    #  Retrieve project information
    try:
        project.get()
        pr_exists = True
    except Exception as err:
        pr_exists = False
        reason = str(err)

    if state == "opened":
        if pr_exists:
            if project.status != "opened":
                # Open project
                project.open()

                # Now verify nodes
                if nodes_state is not None:

                    # Change flag based on the nodes state
                    result["changed"] = nodes_state_verification(
                        expected_nodes_state=nodes_state,
                        nodes_strategy=nodes_strategy,
                        nodes_delay=nodes_delay,
                        poll_wait_time=poll_wait_time,
                        project=project,
                    )
                else:
                    # Means that nodes are not taken into account for idempotency
                    result["changed"] = True
            # Even if the project is open if nodes_state has been set, check it
            else:
                if nodes_state is not None:
                    result["changed"] = nodes_state_verification(
                        expected_nodes_state=nodes_state,
                        nodes_strategy=nodes_strategy,
                        nodes_delay=nodes_delay,
                        poll_wait_time=poll_wait_time,
                        project=project,
                    )

        else:
            module.fail_json(msg=reason, **result)

    elif state == "closed":
        if pr_exists:
            if project.status != "closed":
                # Close project
                project.close()
                result["changed"] = True
        else:
            module.fail_json(msg=reason, **result)

    elif state == "present":
        if pr_exists:
            if nodes_spec is not None:
                # Need to verify if nodes exist
                _nodes_already_created = [node.name for node in project.nodes]
                for node_spec in nodes_spec:
                    if node_spec["name"] not in _nodes_already_created:
                        # Open the project in case it was closed
                        project.open()
                        create_node(node_spec, project, module)
                        result["changed"] = True
            if links_spec is not None:
                for link_spec in links_spec:
                    project.open()
                    # Trigger another get to refresh nodes attributes
                    project.get()
                    # Link verification is already built in the library
                    created = create_link(link_spec, project, module)
                    if created:
                        result["changed"] = True
        else:
            # Create project
            project.create()
            # Nodes section
            if nodes_spec is not None:
                for node_spec in nodes_spec:
                    create_node(node_spec, project, module)
            # Links section
            if links_spec is not None:
                for link_spec in links_spec:
                    create_link(link_spec, project, module)
            result["changed"] = True
    elif state == "absent":
        if pr_exists:
            # Stop nodes and close project to perform delete gracefully
            if project.status != "opened":
                # Project needs to be opened in order to be deleted...
                project.open()
            project.stop_nodes(poll_wait_time=0)
            project.delete()
            result["changed"] = True
        else:
            module.exit_json(**result)

    # Return the project data
    result["project"] = return_project_data(project)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
