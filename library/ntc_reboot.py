#!/usr/bin/env python

# Copyright 2015 Jason Edelman <jason@networktocode.com>
# Network to Code, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

DOCUMENTATION = '''
---
module: ntc_reboot
short_description: Reboot a network device.
description:
    - Reboot a network device, optionally on a timer.
    - Supported platforms: Cisco Nexus switches with NX-API, Cisco IOS switches or routers, Arista switches with eAPI.
Notes:
    - The timer is only supported for IOS devices.
author: Jason Edelman (@jedelman8)
version_added: 1.9.2
requirements:
    - pyntc
options:
    platform:
        description:
            - Switch platform
        required: true
        choices: ['cisco_nxos_nxapi', 'arista_eos_eapi', 'cisco_ios']
    timer:
        description:
            - Time in minutes after which the device will be rebooted.
        required: false
        default: null
    confirm:
        description:
            - Safeguard boolean. Set to true if you're sure you want to reboot.
        required: false
        default: false
    host:
        description:
            - Hostame or IP address of switch.
        required: true
    username:
        description:
            - Username used to login to the target device
        required: true
    password:
        description:
            - Password used to login to the target device
        required: true
    secret:
        description:
            - Enable secret for devices connecting over SSH.
        required: false
    transport:
        description:
            - Transport protocol for API-based devices.
        required: false
        default: https
        choices: ['http', 'https']
    port:
        description:
            - TCP/UDP port to connect to target device. If omitted standard port numbers will be used.
              80 for HTTP; 443 for HTTPS; 22 for SSH.
        required: false
        default: null
'''

EXAMPLES = '''
- ntc_reboot:
    platform: cisco_nxos_nxapi
    confirm: true
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    transport: http

- ntc_file_copy:
    platform: arista_eos_eapi
    confirm: true
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"

- ntc_file_copy:
    platform: cisco_ios
    confirm: true
    timer: 5
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    secret: "{{ secret }}"
'''

RETURN = '''
rebooted:
    description: Whether the device was instructed to reboot.
    returned: success
    type: boolean
    sample: true
'''

try:
    HAS_PYNTC = True
    from pyntc import ntc_device
except ImportError:
    HAS_PYNTC = False

PLATFORM_NXAPI = 'cisco_nxos_nxapi'
PLATFORM_IOS = 'cisco_ios'
PLATFORM_EAPI = 'arista_eos_eapi'

platform_to_device_type = {
    PLATFORM_EAPI: 'eos',
    PLATFORM_NXAPI: 'nxos',
    PLATFORM_IOS: 'ios',
}

def main():
    module = AnsibleModule(
        argument_spec=dict(
            platform=dict(choices=[PLATFORM_NXAPI, PLATFORM_IOS, PLATFORM_EAPI],
                          required=True),
            confirm=dict(required=False, default=False, type='bool', choices=BOOLEANS),
            timer=dict(requred=False, type='int'),
            host=dict(required=True),
            username=dict(required=True, type='str'),
            password=dict(required=True, type='str'),
            secret=dict(required=False),
            transport=dict(default='https', choices=['http', 'https']),
            port=dict(required=False, type='int')
        ),
        supports_check_mode=False
    )

    if not HAS_PYNTC:
        module.fail_json(msg='pyntc Python library not found.')

    platform = module.params['platform']
    host = module.params['host']
    username = module.params['username']
    password = module.params['password']

    transport = module.params['transport']
    port = module.params['port']
    secret = module.params['secret']

    confirm = module.params['confirm']
    timer = module.params['timer']

    if not confirm:
        module.fail_json(msg='confirm must be set to true for this module to work.')

    supported_timer_platforms = [PLATFORM_IOS]

    if timer is not None \
            and platform not in supported_timer_platforms:
        module.fail_json(msg='Timer parameter not supported on platform %s.' % platform)

    kwargs = {}
    if transport is not None:
        kwargs['transport'] = transport
    if port is not None:
        kwargs['port'] = port
    if secret is not None:
        kwargs['secret'] = secret

    device_type = platform_to_device_type[platform]
    device = ntc_device(device_type, host, username, password, **kwargs)

    device.open()

    changed = False
    rebooted = False

    if timer is not None:
        device.reboot(confirm=True, timer=timer)
    else:
        device.reboot(confirm=True)

    changed = True
    rebooted = True

    device.close()
    module.exit_json(changed=changed, rebooted=rebooted)

from ansible.module_utils.basic import *
main()
