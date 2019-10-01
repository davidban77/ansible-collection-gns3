#!/usr/bin/env python

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: gns3_snapshot
short_description: Module that interacts with snapshots of a project on GNS3 server
version_added: '2.8'
description:
    - Module that interacts with snapshots of a project on GNS3 server
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
    snapshot_name:
        description:
            - Snapshot name
        type: str
    snapshot_id:
        description:
            - Snapshot ID
        type: str
    state:
        description:
            - Creates/deletes/restores a project snapshot.
            - NOTE: The restore is not an idempotent task
        type: str
        choices: ['present', 'absent', 'restore']
        required: true
"""

EXAMPLES = """
# Retrieves all the  information from the computes of GNS3 server
- name: Retrieve all the facts of a GNS3 server computes
  gns3_snapshot:
    url: http://localhost
    project_name: demo_lab
    snapshot_name: snap1
    state: present
  register: result

- debug: var=result

# Retrieves only basic facts data of the GNS3 server computes
- gns3_snapshot:
    url: http://localhost
    project_name: demo_lab
    snapshot_id: "SOME_UUID"
    state: absent

# Restores the project from a specific snapshot. This is NOT idempotent
- gns3_snapshot:
    url: http://localhost
    project_name: demo_lab
    snapshot_name: snap1
    state: restore
"""

RETURN = """
created_at:
    description: Unix format datetime
    type: int
name:
    description: Snapshot name
    type: str
project_id:
    description: Project UUID
    type: str
snapshot_id:
    description: Snapshot UUID
    type: dict
"""

import traceback
from ansible.module_utils.basic import AnsibleModule, missing_required_lib

GNS3FY_IMP_ERR = None
try:
    from gns3fy import Gns3Connector, Project

    HAS_GNS3FY = True
except Exception:
    HAS_GNS3FY = False
    GNS3FY_IMP_ERR = traceback.format_exc()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(type="str", required=True),
            user=dict(type="str", default=None),
            password=dict(type="str", default=None, no_log=True),
            port=dict(type="int", default=3080),
            state=dict(
                type="str", required=True, choices=["present", "absent", "restore"]
            ),
            project_name=dict(type="str", default=None),
            project_id=dict(type="str", default=None),
            snapshot_name=dict(type="str", default=None),
            snapshot_id=dict(type="str", default=None),
        ),
        required_one_of=[
            ["project_name", "project_id"],
            ["snapshot_name", "snapshot_id"],
        ],
    )
    result = dict(changed=False)
    if not HAS_GNS3FY:
        module.fail_json(msg=missing_required_lib("gns3fy"), exception=GNS3FY_IMP_ERR)

    server_url = module.params["url"]
    server_port = module.params["port"]
    server_user = module.params["user"]
    server_password = module.params["password"]
    project_name = module.params["project_name"]
    project_id = module.params["project_id"]
    snapshot_name = module.params["snapshot_name"]
    snapshot_id = module.params["snapshot_id"]
    state = module.params["state"]

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

        # Collect project and snapshots data
        project.get()
        snapshot = project.get_snapshot(name=snapshot_name, snapshot_id=snapshot_id)

        if state == "present":
            if snapshot is None:
                # Create the snapshot
                if not snapshot_name:
                    module.fail_json(
                        msg="Need to specify snapshot name for creation", **result
                    )
                project.create_snapshot(name=snapshot_name)
                result["changed"] = True
                result["snapshot"] = project.get_snapshot(
                    name=snapshot_name, snapshot_id=snapshot_id
                )
            else:
                result["snapshot"] = snapshot

        elif state == "absent":
            if snapshot:
                #  Delete snapshot
                project.delete_snapshot(name=snapshot_name, snapshot_id=snapshot_id)
                result["changed"] = True

        elif state == "restore":
            if not snapshot:
                module.fail_json(msg="Snapshot not found", **result)
            # Restore snapshot
            project.restore_snapshot(name=snapshot_name, snapshot_id=snapshot_id)
            result["changed"] = True
            result["snapshot"] = snapshot

        module.exit_json(**result)
    except Exception as err:
        module.fail_json(msg=str(err), **result)


if __name__ == "__main__":
    main()
