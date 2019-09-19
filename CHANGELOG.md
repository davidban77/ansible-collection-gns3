# Releases

## 1.2.2.

- Upgrading to `gns3fy ^0.4.0`

## 1.2.1

Enhancement:

- No more `node_type` needed when creating nodes in a project.

## 1.2.0

New features:

- Modules:
    - `gns3_nodes_inventory`: Returns inventory-style dictionary of the nodes.

Fixes:

- Modules:
    - Error when using the `gns3_version` module when `gns3fy` is not installed

- Tests:
    - Added check for `gns3_version`

## 1.1.0

New features:

- Roles:
    - `create_lab`: Create a GNS3 Lab by creating a project and starting up the nodes
    - `delete_lab`: Deletes a GNS3 Lab by stopping nodes and deleting the project

## 1.0.1

Initial push of the ansible collections. Released focused on the `gns3` module
