#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: gcloud

short_description: Gcloud Module to Create, Terminate, Start, Stop VMS

version_added: "2.4"

description:
    - "Gcloud Module to Create, Terminate, Start, Stop VMS"

extends_documentation_fragment:
    - GigeNET Cloud

author:
    - Scott Ehas
'''

from ansible.module_utils.basic import AnsibleModule
import boto, time

def run_module():

    module_args = dict(
        gcloud_url=dict(type='str', required=False, default="https://api.thegcloud.com"),
        gcloud_access_key=dict(type='str', required=True),
        gcloud_secret_key=dict(type='str', required=True),
        id=dict(type='int', required=False),
        image=dict(type='str', required=False),
        instance_type=dict(type='str', required=False),
        count=dict(type='int', required=False, default=1),
        private_ip=dict(type='bool', required=False, default=False),
        state=dict(type='str', required=False, default="present"),
        zone=dict(type='str', required=False, default="ord1"),
        tag=dict(type='str', required=False),
        wait_for=dict(type='int', required=False, default=0),
    )

    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        return result

    gcloud_url = module.params['gcloud_url']
    gcloud_access_key = module.params['gcloud_access_key']
    gcloud_secret_key = module.params['gcloud_secret_key']

    if module.params['id']:
        id = module.params['id']
    else:
        id = None

    if module.params['image']: 
        image = module.params['image']
    else:
        image = None

    if module.params['instance_type']:
        instance_type = module.params['instance_type']
    else:
        instance_type = None

    count = module.params['count']
    private_ip = module.params['private_ip']
    state = module.params['state']
    zone = module.params['zone']

    if module.params['tag']: 
        tag = module.params['tag']
    else:
        tag = None

    wait_for = module.params['wait_for']

    fail_msg = ""
    try:
        conn = boto.connect_ec2_endpoint(gcloud_url, gcloud_access_key, gcloud_secret_key)
    except Exception as e:
        fail_msg = "Unable to connect to region: %s" % gcloud_url
        module.fail_json(msg=fail_msg, **result)

    try:
        if state == "present":
            if id and instance_type:
                conn.modify_instance_attribute(instance_id=id, attribute="InstanceType", value=instance_type)
                result['changed']=True
                result['message']="VM Action was successful"
                module.exit_json(**result)

            if not image:
                result['message']="Image attribute required on create"
                module.fail_json(msg=result['message'], **result)
        
            valid=False
            for v in conn.get_all_images():
                if v.name == image:
                    valid=True  

            if not valid:
                result['message']="Image selected is invalid: %s" % image
                module.fail_json(msg=result['message'], **result)

            if not instance_type:
                result['message']="Instance type required on create"
                module.fail_json(msg=result['message'], **result)

            valid=False
            for v in conn.get_all_zones():
                if v.name == zone:
                   valid=True

            if not valid:
                result['message']="Zone selected is invalid: %s" % image
                module.fail_json(msg=result['message'], **result)          

            instances = []
            if private_ip == True:
                for idx in range(count):
                    instanceId = conn.run_instances(image_id=image, instance_type=instance_type, placement=zone, private_ip_address=True)
                    instances.append({"instance_id": instanceId.instances[0].id, "ip_address": instanceId.instances[0].publicIpAddress, \
                        "password": conn.get_password_data(instanceId.instances[0].id)})
                    if tag:
                        conn.create_tags([instanceId.instances[0].id], { tag: ''})
            else:
                for idx in range(count):
                    instanceId = conn.run_instances(image_id=image, instance_type=instance_type, placement=zone, private_ip_address=False)
                    instances.append({"instance_id": instanceId.instances[0].id, "ip_address": instanceId.instances[0].publicIpAddress, \
                        "password": conn.get_password_data(instanceId.instances[0].id)})
                    if tag:
                        conn.create_tags([instanceId.instances[0].id], { tag: ''})

            elapsed_time = 0
            start_time = time.time()
            while elapsed_time < wait_for:
                time.sleep(5)
                elapsed_time = time.time() - start_time
                break_loop = True
                for instance in instances:
                    status = conn.get_all_instance_status(instance['instance_id'])[0].state_code
                    if status != 0:
                        break_loop = False
                if break_loop:
                    break

            if wait_for > 0:
                for instance in instances:
                    status = conn.get_all_instance_status(instance['instance_id'])[0].state_code
                    if status != 0:
                        raise Exception("Timeout exceeded on wait_for parameter")

            result['instances'] = instances

        elif not id or state not in ['running', 'restarted', 'stopped', 'absent']:
            result['message'] = "Failed"
            if not id:
                fail_msg = 'State attribute requires a valid ID'
            else:
                fail_msg = 'State attribute requires a valid state'
        elif state == "running":
            conn.start_instances(instance_ids=[id])
        elif state == "restarted":
            conn.reboot_instances(instance_ids=[id])
        elif state == "stopped":
            conn.stop_instances(instance_ids=[id]) 
        elif state == "absent":
            conn.terminate_instances(instance_ids=[id])
    except Exception as e:
        fail_msg=e

    if fail_msg:
        result['message']="VM Action was unsuccessful"
        module.fail_json(msg=fail_msg, **result)

    result['changed']=True
    result['message']="VM Action was successful"

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()