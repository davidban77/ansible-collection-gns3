#!/usr/bin/env python

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: gns3_facts
short_description: Module that retrieves the compute(s) information of a GNS3 server
version_added: '2.8'
description:
    - Module that retrieves the compute(s) information of a GNS3 server
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
    get_images:
        description:
            - If set it will also retrieve the images of the specified emulator unless
            - is set to 'all', in which case will retrieve from all emulators. For a
            - list of available emulators, visit the GNS3 API information
        type: str
    get_compute_ports:
        description:
            - If set it will retrieve the console_ports and udp_ports of the compute
        type: bool
"""

EXAMPLES = """
# Retrieves all the  information from the computes of GNS3 server
- name: Retrieve all the facts of a GNS3 server computes
  gns3_facts:
    url: http://localhost
    get_images: all
    get_compute_ports: yes
  register: computes_info

- debug: var=computes_info

# Retrieves only basic facts data of the GNS3 server computes
- gns3_facts:
    url: http://localhost
  register: computes_info

- debug: var=computes_info
"""

RETURN = """
compute_id:
    description: Server identifier
    type: str
name:
    description: Server name
    type: str
host:
    description: Server host
    type: str
capabilities:
    description: Object that describes what the server supports
    type: dict
connected:
    description: Whether the controller is connected to the compute or not
    type: bool
cpu_usage_percent:
    description: CPU usage of the compute
    type: float
memory_usage_percent:
    description: RAM usage of the compute
    type: int
port:
    description: Server port
    type: int
protocol:
    description: Protocol used (http, https)
    type: str
user:
    description: User for authentication
    type: str
last_error:
    description: Last error on the compute
    type: str
images:
    description: Images configured on the compute depending on the emulator (optional)
    type: dict
compute_ports:
    description: Ports used by the compute (console and udp ports) (optional)
    type: dict
"""

import traceback
from ansible.module_utils.basic import AnsibleModule, missing_required_lib

GNS3FY_IMP_ERR = None
try:
    from gns3fy import Gns3Connector

    HAS_GNS3FY = True
except Exception:
    HAS_GNS3FY = False
    GNS3FY_IMP_ERR = traceback.format_exc()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(type="str", required=True),
            port=dict(type="int", default=3080),
            user=dict(type="str", default=None),
            password=dict(type="str", default=None, no_log=True),
            get_images=dict(type="str", default=None),
            get_compute_ports=dict(type="bool", default=False),
        )
    )
    result = dict(changed=False)
    if not HAS_GNS3FY:
        module.fail_json(msg=missing_required_lib("gns3fy"), exception=GNS3FY_IMP_ERR)

    server_url = module.params["url"]
    server_port = module.params["port"]
    server_user = module.params["user"]
    server_password = module.params["password"]
    get_images = module.params["get_images"]
    get_compute_ports = module.params["get_compute_ports"]

    try:
        # Create server session
        server = Gns3Connector(
            url=f"{server_url}:{server_port}", user=server_user, cred=server_password
        )

        computes = server.get_computes()
        for compute in computes:

            # Images
            if get_images:
                compute["images"] = dict()

                if get_images == "all":
                    for emulator in compute["capabilities"]["node_types"]:
                        try:
                            compute["images"][emulator] = server.get_compute_images(
                                emulator=emulator, compute_id=compute["compute_id"]
                            )
                        except Exception as err:
                            if "404" in str(err):
                                # Contine if no image dir is set for that emulator
                                continue
                else:
                    compute["images"][get_images] = server.get_compute_images(
                        emulator=get_images, compute_id=compute["compute_id"]
                    )

            # Compute ports
            if get_compute_ports:
                compute["compute_ports"] = server.get_compute_ports(
                    compute_id=compute["compute_id"]
                )

        result["facts"] = computes
        module.exit_json(**result)
    except Exception as err:
        module.fail_json(msg=str(err), **result)


if __name__ == "__main__":
    main()
