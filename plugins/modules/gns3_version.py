#!/usr/bin/env python

ANSIBLE_METADATA = {
    'metadata_version': '1.2',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: gns3_version
short_description: Retrieves GNS3 server version
version_added: "2.8"
description:
    - "Retrieves GNS3 server version using gns3fy"
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
'''

EXAMPLES = '''
# Retrieve the GNS3 server version
- name: Get the server version
  gns3_version:
    url: http://localhost
    port: 3080
  register: result

- debug: var=result
'''

RETURN = '''
local_compute:
    description: Whether this is a local server or not
    type: bool
    returned: always
version:
    description: Version number of the server
    type: str
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from gns3fy import Gns3Connector


def main():
    module_args = dict(
        url=dict(type="str", required=True),
        port=dict(type="int", default=3080),
    )
    result = dict(
        changed=False,
        local_compute=None,
        version=None
    )
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    if module.check_mode:
        module.exit_json(**result)

    server = Gns3Connector(url=f"{module.params['url']}:{module.params['port']}")
    _version = server.get_version()
    result.update(
        local_compute=_version["local"],
        version=_version["version"]
    )
    module.exit_json(**result)


if __name__ == "__main__":
    main()
