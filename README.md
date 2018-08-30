
######### Gcloud Ansible Playbook Demo #########

- name: Gcloud Module Demo
  connection: local
  hosts: localhost

  tasks:
  - gcloud:
      gcloud_url: 'https://api.thegcloud.com'
      gcloud_access_key: 'ACCESS_KEY'
      gcloud_secret_key: 'SECRET_KEY'
      instance_type: "gcl.1"
      image: "centos64_7"
      state: "present"
      zone: "ord1"
      private_ip: True
      count: 1
      tag: DemoVM
      wait_for: 240
    register: gateways