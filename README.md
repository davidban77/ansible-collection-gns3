# Ansible Module for GNS3
Ansible module repository for GNS3 Server REST API using [gns3fy - see the docs](https://davidban77.github.io/gns3fy/).

## Installation

For the module to be used you need to have installed [gns3](https://github.com/davidban77/gns3fy)

```
pip install gns3fy
```

This collections is packaged under ansible-galaxy, so to install it you need [mazer from Ansible Projects](https://galaxy.ansible.com/docs/mazer/index.html):

```
mazer install davidban77.gns3
```

## Features

- Open/closes projects
- Starts/stops all nodes inside a project, or it can be done sequentially with a delay factor
- Creates/Updates projects with nodes and links specified as variables in a playbook.
- Deletes projects safely by stopping nodes if there are, closing the project and finally deleting it.
- Idempotency in all actions. For example if a playbook creates a project with some nodes, it will not recreate them if the palybook is rerun.


## Modules

These are the modules provided with this collection:

- `gns3_version`: Retrieves GNS3 server version
- `gns3_project`: Module to interact with GNS3 server projects
    - It **opens/closes projects** and performs basic turnup/teradown operations on nodes.
    - It **creates/updates or deletes projects**, with the respective nodes and links specified

## Examples

Here are some examples of how to use the module.

#### Get server version

```yaml
---
- host: localhost
  # Call the collections to use the respective modules
  collections:
    - davidban77.gns3
  vars:
    gns3_url: http://localhost
  tasks:
    - name: Get the server version
    gns3_version:
        url: "{{ gns3_url }}"
        port: 3080
    register: result

    - debug: var=result
```

#### Manipulate GNS3 projects

```yaml
---
# Open a GNS3 project
- name: Start lab
  gns3_project:
    url: "{{ gns3_url }}"
    state: opened
    project_name: lab_example

# Stop all nodes inside an open project
- name: Stop nodes
  gns3_project:
    url: "{{ gns3_url }}"
    state: opened
    project_name: lab_example
    nodes_state: stopped
    nodes_strategy: all
    poll_wait_time: 5

# Open a GNS3 project and start nodes one by one with a delay of 10sec between them
- name: Start nodes one by one
  gns3_project:
    url: "{{ gns3_url }}"
    state: opened
    project_name: lab_example
    nodes_state: started
    nodes_strategy: one_by_one
    nodes_delay: 10

# Close a GNS3 project
- name: Stop lab
  gns3_project:
    url: "{{ gns3_url }}"
    state: closed
    project_id: "UUID-SOMETHING-1234567"
```

#### Create and delete projects

```yaml
---
# Create a GNS3 project given nodes and links specifications
- name: Create a project
  gns3_project:
    url: "{{ gns3_url }}"
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
        - ['alpine-1', 'eth0', 'alpine-2', 'eth1']

# Delete a GNS3 project
- name: Delete project
  gns3_project:
    url: "{{ gns3_url }}"
    state: absent
    project_name: new_lab
```
