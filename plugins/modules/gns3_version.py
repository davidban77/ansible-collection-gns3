#!/usr/bin/env python

ANSIBLE_METADATA = {
    "metadata_version": "1.2",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: gns3_version
short_description: Retrieves GNS3 server version
version_added: '2.8'
description:
    - 'Retrieves GNS3 server version using gns3fy'
requirements: [ gns3fy ]
author:
    - David Flores (@netpanda)
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
"""

EXAMPLES = """
# Retrieve the GNS3 server version
- name: Get the server version
  gns3_version:
    url: http://localhost
    port: 3080
  register: result

- debug: var=result
"""

RETURN = """
local_compute:
    description: Whether this is a local server or not
    type: bool
    returned: always
version:
    description: Version number of the server
    type: str
    returned: always
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
            url=dict(type="str", required=True), port=dict(type="int", default=3080)
        )
    )
    if not HAS_GNS3FY:
        module.fail_json(msg=missing_required_lib("gns3fy"), exception=GNS3FY_IMP_ERR)
    result = dict(changed=False, local_compute=None, version=None)

    server = Gns3Connector(url=f"{module.params['url']}:{module.params['port']}")
    _version = server.get_version()
    result.update(local_compute=_version["local"], version=_version["version"])
    module.exit_json(**result)


if __name__ == "__main__":
    main()
