# Ansible Module for GNS3
[Ansible-Galaxy collections](https://galaxy.ansible.com/davidban77/gns3) repository for GNS3 Server REST API using [gns3fy - see the docs](https://davidban77.github.io/gns3fy/).

## Installation

For the module to be used you need to have installed [gns3fy](https://github.com/davidban77/gns3fy)

```
pip install gns3fy
```

This collections is packaged under ansible-galaxy, so to install it you need [mazer from Ansible Projects](https://galaxy.ansible.com/docs/mazer/index.html):

```
mazer install davidban77.gns3
```

## Features

- Open/closes projects.
- Starts/stops all nodes inside a project, or it can be done sequentially with a delay factor.
- Creates/Updates projects with nodes and links specified as variables in a playbook.
- Deletes projects safely by stopping nodes, if there are any, then closing the project and finally deleting it.
- Creates/Deletes/Restores snapshots of projects.
- Retrieves information about available emulators on the GNS3 server compute, as well as available images, console ports, version, etc..
- Idempotency is present in all actions. An example could be reflected in a playbook that creates a project with nodes and links, these settings will not be executed again on a rerun (and by settings I mean projects settings, nodes and links)/


## Modules

These are the modules provided with this collection:

- `gns3_version`: Retrieves GNS3 server version. (**TO BE DEPRECATED** with the `gns3_facts` module)
- `gns3_facts`: Retrieves the compute(s) information of a GNS3 server
- `gns3_project`: Module to interact with GNS3 server projects
    - It opens/closes projects and performs basic turnup/teradown operations on nodes.
    - It creates/updates or deletes projects, with the respective nodes and links specified
- `gns3_project_file`: Updates/creates a file on a project directory.
- `gns3_snapshot`: Module that interacts with snapshots of a project on GNS3 server.
- `gns3_node`: Module to operate a node in a GNS3 server project.
- `gns3_node_file`: Updates/creates a file on a node directory.
- `gns3_nodes_inventory`: Retrieves GNS3 a project nodes console information.

## Examples: using the module

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
    - name: Get the server facts
      gns3_facts:
        url: "{{ gns3_url }}"
        port: 3080
        get_images: all
        get_compute_ports: yes
      register: result

    - debug: var=result
```
#### Get nodes_inventory information from a project

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
      gns3_nodes_inventory:
        url: "{{ gns3_url }}"
        project_name: lab_example
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
          template: alpine
        - name: alpine-2
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

## Examples: using the roles

There are also some convinient roles that you can use to manage your labs. Here is an example playbook:

`main.yml`
```yaml
- hosts: localhost
  tasks:
    - import_role:
        name: create_lab
      when: execute == "create"
    - import_role:
        name: delete_lab
      when: execute == "delete"
```

This way you can call and switch the behaviour of the playbook:

**Create the lab**
```
ansible-playbook main.yml -e execute=create
```

Or **delete the lab**
```
ansible-playbook main.yml -e execute=delete
```

Here is the example variable file which specifies the naming convention used. You can see that the variable names come from the module itself with only `gns3_`

```yaml
---
gns3_url: "http://dev_gns3server"
gns3_project_name: test_ansible
gns3_nodes_spec:
    - name: veos-1
      template: "vEOS-4.21.5F"
    - name: veos-2
      template: "vEOS-4.21.5F"
    - name: ios-1
      template: "IOU-15.4"
    - name: ios-2
      template: "IOU-15.4"
gns3_nodes_strategy: one_by_one
gns3_links_spec:
    - ["veos-1", "Ethernet1", "veos-2", "Ethernet1"]
    - ["veos-1", "Ethernet2", "ios-1", "Ethernet1/0"]
    - ["veos-2", "Ethernet2", "ios-2", "Ethernet1/0"]
    - ["ios-1", "Ethernet1/2", "ios-2", "Ethernet1/2"]
```

### More examples

For more examples like create an `/etc/network/interfaces` file for an `alpine` docker node to configure its network interfaces, or restore a project to an specific snapshot, you can go to the `test/playbooks` directory.
