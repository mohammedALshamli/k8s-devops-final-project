# VM Specifications — Path B (VMware Workstation)

| Field           | cp1 (Control Plane)     | w1 (Worker)           
|-----------------|--------------------------|---------------------------|
| Hostname        | k8slab-cp1               | k8slab-w1                 |
| Private IP      | 10.0.1.10                | 10.0.1.11                 |
| vCPU            | 2                        | 2                          |
| RAM             | 4 GB                     | 4 GB                      |
| Disk            | 40 GB                    | 40 GB                     |
| OS              | Rocky Linux 9            | Rocky Linux 9              |
| Network Mode    | NAT (VMnet8, custom subnet 10.0.1.0/24) | NAT (VMnet8, custom subnet 10.0.1.0/24) |
| SSH User        | ouda                     | ouda                       |
| SSH Key         | ~/.ssh/k8slab_key        | ~/.ssh/k8slab_key          |

## Verification

- \ping\ test between cp1 and w1: successful
- Passwordless SSH from laptop to both VMs: confirmed
- \/etc/hosts\ updated on both VMs with each other's hostname/IP
