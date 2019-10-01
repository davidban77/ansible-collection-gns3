# Releases

## 1.5.0

**Enhancements:**

- Added `gns3_facts` to retrieve the compute information like: console ports, server version, available emulators, available images, etc..
- Added `gns3_snapshot` to manipulate the snapshot creation/deletion and restoration of a project.

**Fixes:**

- Added the needed `user` and `password` arguments to all the modules, when interacting with a GNS3 server with authentication.
- Refactored the modules a little to be more standard with each other.

## 1.4.0

**Enhacements:**

- Added `gns3_node` to interact with the node inside a project. Provides the following:
    - `start/stop/suspend/reload`: Actions to be applied on the node. These are idempotent with the exception of `reload`.
    - Special flags like `retry` for an action to be applied a second time just in case... And a `force_project_open` to interact with a device if the project is closed
- Refactored `gns3_project` to be more pythonic

## 1.3.0

**Enhancements:**

- Added `gns3_node_file` and `gns3_project_file` modules.
- Improved the Makefile
- Added alpine node to the tests

## 1.2.2.

**Fixes:**

- Upgrading to `gns3fy ^0.4.0`

## 1.2.1

**Enhancements:**

- No more `node_type` needed when creating nodes in a project.

## 1.2.0

**Enhancements:**

- Modules:
    - `gns3_nodes_inventory`: Returns inventory-style dictionary of the nodes.

**Fixes:**

- Modules:
    - Error when using the `gns3_version` module when `gns3fy` is not installed

- Tests:
    - Added check for `gns3_version`

## 1.1.0

**Enhancements:**

- Roles:
    - `create_lab`: Create a GNS3 Lab by creating a project and starting up the nodes
    - `delete_lab`: Deletes a GNS3 Lab by stopping nodes and deleting the project

## 1.0.1

Initial push of the ansible collections. Released focused on the `gns3` module
