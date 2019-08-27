#!/usr/bin/env python

# Copyright: (c) 2018, David Flores <davidflores7_8@hotmail.com>
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: gns3

short_description: Module to interact with GNS3 server projects

version_added: "2.8"

description:
    - "Module to interact with GNS3 server projects. It is using the L(gns3fy library,
    https://davidban77.github.io/gns3fy/)"
    - It opens/closes projects and performs basic turnup/teradown operations on nodes.
    - It creates/updates or deletes projects, with the respective nodes and links
    specified

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
    state:
        description:
            - State of the project to be on the GNS3 server
            - "- C(opened): Opens a project and turns up nodes"
            - "- C(closed): Closes a project and turns down nodes"
            - "- C(present): Creates/update a project on the server"
            - "- C(absent): Deletes a project on the server"
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
            - "- C(all): It starts/stops all nodes at once"
            - "- C(one_by_one): It starts/stops nodes serialy using I(nodes_delay) time
            between each action"
            - Used when I(state) is C(opened)/C(closed)
        type: str
        choices: ['all', 'one_by_one']
        default: 'all'
    nodes_delay:
        description:
            - Delay time in seconds to wait between nodes start/stop
            - Used when I(nodes_strategy) is C(one_by_one)
        type: int
    poll_wait_time:
        description:
            - Delay in seconds to wait to poll nodes when they are started/stopped.
            - Used when I(nodes_state) is C(started)/C(stopped)
        type: int
        default: 5
    nodes_spec:
        description:
            - List of dictionaries specifying the nodes properties.
            - "- Mandatory attributes: C(name), C(node_type) and C(template)."
            - "- Optional attributes: C(compute_id). It defaults to C(local)"
        type: list
    links_spec:
        description:
            - "List of lists specifying the links endpoints. Example: C(- ['alpine-1',
            'eth0', 'alpine-2', 'eth0'])"
            - "Mandatory attributes: C(node_a), C(port_a), C(node_b) and C(port_b)"
        type: list


author:
    - David Flores (twitter - @netpanda)
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
    state: stopped
    project_id: "UUID-SOMETHING-1234567"

# Create a GNS3 project
- name: Create a project given an specifications file
  gns3_project:
    url: http://localhost
    state: create
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
- name: Test failure of the module
  gns3_project:
    url: http://localhost
    state: delete
    project_name: new_lab
"""

RETURN = """
message:
    description: The output message that the test module generates
    type: str
    returned: always
"""

import time
import traceback
from ansible.module_utils.basic import AnsibleModule, missing_required_lib

LIB_IMP_ERR = None
try:
    from gns3fy import Gns3Connector, Project

    HAS_LIB = True
except Exception:
    HAS_LIB = False
    LIB_IMP_ERR = traceback.format_exc()


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


def nodes_state_verification(module, project, result):
    "Verifies each node state and returns a changed attribute"
    nodes_statuses = [node.status for node in project.nodes]
    expected_state = module.params["nodes_state"]

    # Verify if nodes do not match expected state
    if expected_state == "started" and any(
        status == "stopped" for status in nodes_statuses
    ):
        # Turnup the nodes based on strategy
        if module.params["nodes_strategy"] == "all":
            project.start_nodes(poll_wait_time=module.params["poll_wait_time"])
        elif module.params["nodes_strategy"] == "one_by_one":
            for node in project.nodes:
                if node.status != "started":
                    node.start()
                    time.sleep(module.params["nodes_delay"])
        result["changed"] = True
    elif expected_state == "stopped" and any(
        status == "started" for status in nodes_statuses
    ):
        # Shutdown nodes based on strategy
        if module.params["nodes_strategy"] == "all":
            project.stop_nodes(poll_wait_time=module.params["poll_wait_time"])
        elif module.params["nodes_strategy"] == "one_by_one":
            for node in project.nodes:
                if node.status != "stopped":
                    node.stop()
                    time.sleep(module.params["nodes_delay"])
        result["changed"] = True
    # if no match then there are no changes on the nodes to perform


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
    except Exception as err:
        module.fail_json(msg=str(err), exception=traceback.format_exc())
    return True


def main():
    module_args = dict(
        url=dict(type="str", required=True),
        port=dict(type="int", default=3080),
        state=dict(
            type="str",
            required=True,
            choices=["opened", "closed", "present", "absent"],
        ),
        project_name=dict(type="str", default=None),
        project_id=dict(type="str", default=None),
        nodes_state=dict(type="str", choices=["started", "stopped"]),
        nodes_strategy=dict(type="str", choices=["all", "one_by_one"], default="all"),
        nodes_delay=dict(type="int"),
        poll_wait_time=dict(type="int", default=5),
        nodes_spec=dict(type="list"),
        links_spec=dict(type="list"),
    )
    result = dict(changed=False)
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[["project_name", "project_id"]],
        required_if=[["nodes_strategy", "one_by_one", ["nodes_delay"]]],
    )
    if not HAS_LIB:
        module.fail_json(msg=missing_required_lib("gns3fy"), exception=LIB_IMP_ERR)
    if module.check_mode:
        module.exit_json(**result)

    # Create server session
    server = Gns3Connector(url=f"{module.params['url']}:{module.params['port']}")
    # Define the project
    if module.params["project_name"] is not None:
        project = Project(name=module.params["project_name"], connector=server)
    elif module.params["project_id"] is not None:
        project = Project(project_id=module.params["project_id"], connector=server)

    try:
        project.get()
        pr_exists = True
    except Exception as err:
        pr_exists = False
        reason = str(err)

    if module.params["state"] == "opened":
        if pr_exists:
            if project.status != "opened":
                # Open project
                project.open()

                # Now verify nodes
                if module.params["nodes_state"] is not None:

                    # Change flag based on the nodes state
                    nodes_state_verification(module, project, result)
                else:
                    # Means that nodes are not taken into account for idempotency
                    result["changed"] = True
            # Even if the project is open if nodes_state has been set, check it
            else:
                if module.params["nodes_state"] is not None:
                    nodes_state_verification(module, project, result)

        else:
            module.fail_json(msg=reason, **result)

    elif module.params["state"] == "closed":
        if pr_exists:
            if project.status != "closed":
                # Close project
                project.close()
                result["changed"] = True
        else:
            module.fail_json(msg=reason, **result)

    elif module.params["state"] == "present":
        if pr_exists:
            if module.params["nodes_spec"] is not None:
                # Need to verify if nodes exist
                _nodes_already_created = [node.name for node in project.nodes]
                for node_spec in module.params["nodes_spec"]:
                    if node_spec["name"] not in _nodes_already_created:
                        # Open the project in case it was closed
                        project.open()
                        create_node(node_spec, project, module)
                        result["changed"] = True
            if module.params["links_spec"] is not None:
                for link_spec in module.params["links_spec"]:
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
            if module.params["nodes_spec"] is not None:
                for node_spec in module.params["nodes_spec"]:
                    create_node(node_spec, project, module)
            # Links section
            if module.params["links_spec"] is not None:
                for link_spec in module.params["links_spec"]:
                    create_link(link_spec, project, module)
            result["changed"] = True
    elif module.params["state"] == "absent":
        if pr_exists:
            # Stop nodes and close project to perform delete gracefully
            project.stop_nodes(poll_wait_time=0)
            project.close()
            project.delete()
            result["change"] = True

    # Return the project data
    result["project"] = return_project_data(project)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
