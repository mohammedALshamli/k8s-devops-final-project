# k8s-devops-final-project

DevOps Bootcamp Final Capstone — Path B (VMware Workstation)  
**Author:** Mohammed Alshamli  
**Cluster Architecture:** 2-Node Kubernetes Cluster on Rocky Linux 9 (VMware NAT `10.0.1.0/24`)

---

## Architecture & Cluster Specifications

| Hostname | Role | IP Address | vCPU | RAM | Disk | OS | Container Runtime | Kubernetes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `k8slab-cp1` | Control Plane & Controller | `10.0.1.10` | 2 | 4 GB | 40 GB | Rocky Linux 9.8 | containerd 2.3.6 (systemd) | v1.36.5 |
| `k8slab-w1` | Worker Node | `10.0.1.11` | 2 | 4 GB | 40 GB | Rocky Linux 9.8 | containerd 2.3.6 (systemd) | v1.36.5 |

* Network: VMware NAT (VMnet8), Gateway: `10.0.1.2`, Laptop Host Interface: `10.0.1.1`
* Pod Network CIDR: `192.168.0.0/16` (Calico CNI v3.31.0)
* Automation User: `mohamed` (passwordless sudo, key-based SSH)

---

## Quick Reproduction Commands

### 1. Repository Setup & Laptop Tools
```bash
# Clone the repository
git clone https://github.com/mohammedALshamli/k8s-devops-final-project.git
cd k8s-devops-final-project

# Verify tools on workstation
git --version
ssh -V
python --version
terraform -version
```

### 2. SSH Access to Nodes
```bash
# SSH into Control Plane
ssh -i ~/.ssh/k8slab_key ouda@10.0.1.10

# SSH into Worker Node
ssh -i ~/.ssh/k8slab_key ouda@10.0.1.11
```

### 3. Terraform Validation (Task 5)
```bash
cd terraform
terraform fmt -check
terraform init
terraform validate
cd ..
```

### 4. Cluster Automation via Ansible (Tasks 10–15)
```bash
# On cp1 (as user mohamed):
cd /home/mohamed/k8s-devops-final-project/ansible

# Test connectivity
ansible -i inventory.ini k8s_cluster -m ping -b

# Run full cluster deployment in one shot
ansible-playbook -i inventory.ini site.yml
```

### 5. Verify Kubernetes Cluster
```bash
# On cp1 (as user mohamed):
kubectl get nodes -o wide
kubectl get pods -A
```

### 6. Run Application Locally with Docker Compose (Task 17)
```powershell
# In project root on laptop (Docker Desktop running):
docker compose up -d --build

# Verify endpoints (mapped to host port 5050 due to WinNAT)
curl http://localhost:5050/health
curl http://localhost:5050/ready

# Run unit tests
python -m pytest app/ -v
```

---

## Task 1 — Project Repository & Git Hygiene

### Implementation Summary
* Created repository directory structure: `terraform/`, `ansible/`, `app/`, `k8s/`, `docs/screenshots/`.
* Configured `.gitignore` to prevent credential and state leakage.
* Initialized Git with clean commit hygiene following standard semantic prefixes (`feat`, `fix`, `chore`, `docs`).

### Concept Questions & Answers

**Q1: Which files/directories are excluded by `.gitignore` and why?**
> **Answer:** 
> * `*.tfstate*`: Leaks cloud resource IDs, private network IP addresses, and potentially sensitive variables in plaintext.
> * `.terraform/`: Large local provider cache binaries that are automatically regenerated via `terraform init`.
> * `terraform.tfvars`: Contains user-specific values and real subscription/secret credentials.
> * `*.pem`, `id_ed25519*`, `k8slab_key*`: Private SSH keys that prove user identity and must never leave the local machine.
> * `kubeconfig`, `admin.conf`: Provide cluster administrative control; checking them in compromises the entire Kubernetes cluster.
> * `app/instance/*.db`, `app/__pycache__/`, `app/.pytest_cache/`: Ephemeral local databases and Python runtime caches.

**Q2: If a secret is accidentally committed and later deleted in a subsequent commit, is it safe?**
> **Answer:** No. Git is an append-only directed acyclic graph (DAG). A deleted file remains permanently preserved in historical commit blobs, branch history, and the Git reflog. Anyone cloning or fetching the repository can extract the historical commit. The compromised secret must be immediately revoked and rotated, not just removed from HEAD.

---

## Task 2 — Workstation Tool Verification

### Implementation Summary
Verified required tooling on the host machine:
* `git` version 2.45+
* `OpenSSH` (ssh client)
* `python` 3.12+ / 3.14
* `terraform` v1.9+
* `VMware Workstation Pro` 17

---

## Task 4 — SSH Key Pair Generation

### Implementation Summary
* Generated an Ed25519 SSH keypair dedicated for the lab:
  ```bash
  ssh-keygen -t ed25519 -f ~/.ssh/k8slab_key -C "k8slab"
  ```
* Installed the public key (`k8slab_key.pub`) onto both virtual machines (`k8slab-cp1` and `k8slab-w1`).

### Concept Questions & Answers

**Q1: What is the security difference between the private key and public key?**
> **Answer:** The public key (`.pub`) can be freely shared and is placed in `~/.ssh/authorized_keys` on destination servers to authorize access. The private key proves identity, is stored locally with restricted file permissions (`chmod 600`), and must never be shared or transferred across machines.

---

## Task 5 — Terraform Code (Write & Validate)

### Implementation Summary
* Authored standard declarative infrastructure manifests in `terraform/`:
  * `providers.tf`: Provider declarations pinned to `hashicorp/azurerm ~> 4.0`.
  * `variables.tf`: Input variable schema for region, resource group, and VM definitions.
  * `network.tf`: Virtual network (`10.0.0.0/16`), subnet (`10.0.1.0/24`), and NSG security rules.
  * `vms.tf`: VM instances iterating over node maps with fixed private IPs (`10.0.1.10`, `10.0.1.11`).
  * `cloud-init.tftpl`: Automation cloud-init script for user provisioning.
  * `outputs.tf`: Exported IP addresses and connection strings.
* Validated syntax and configuration: `terraform validate` returned **Success! The configuration is valid**.

### Concept Questions & Answers

**Q1: Why does the Network Security Group (NSG) not need explicit rules for cp1 ↔ w1 internal traffic?**
> **Answer:** Intra-subnet and intra-VNet traffic is permitted by default in virtual network architectures. Security group rules primarily filter and restrict external traffic entering the virtual network boundary from the public internet.

**Q2: Why must private IPs assigned to Kubernetes nodes be static?**
> **Answer:** `kubeadm init`, cluster TLS certificates (SANs), etcd peer endpoints, `/etc/hosts` mappings, and join tokens are bound to specific IP addresses. If node IPs change dynamically via DHCP, certificate validation fails, etcd quorum breaks, and cluster communication collapses.

**Q3: What information is stored in `terraform.tfstate`?**
> **Answer:** `terraform.tfstate` maps declared configuration to real-world resources. It stores complete metadata, resource IDs, IP addresses, relationships, and sensitive input/output attributes in unencrypted plaintext.

---

## Task 6B — VMware Workstation Alternative

### Implementation Summary
* Created two virtual machines using Rocky Linux 9 Minimal ISO:
  * `k8slab-cp1`: 2 vCPU, 4 GB RAM, 40 GB disk, IP `10.0.1.10`
  * `k8slab-w1`: 2 vCPU, 4 GB RAM, 40 GB disk, IP `10.0.1.11`
* Configured VMware NAT network (`VMnet8`, `10.0.1.0/24`).
* Configured `/etc/hosts` and persistent hostnames on both nodes.
* Verified mutual network reachability (0% packet loss). Specifications documented in `docs/vm-specs.md`.

---

## Task 7 — Automation User Setup

### Implementation Summary
* Created automation user `mohamed` on both `cp1` and `w1`:
  ```bash
  sudo useradd -m -G wheel mohamed
  echo "mohamed ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/mohamed
  sudo chmod 0440 /etc/sudoers.d/mohamed
  ```
* Validated sudo syntax with `sudo visudo -c`.

### Concept Questions & Answers

**Q1: Why does cp1 need passwordless sudo if it is already the Ansible controller?**
> **Answer:** In this architecture, `cp1` is both the controller and a managed target (`ansible_connection=local`). System-level tasks (e.g., package installation, kernel tuning, containerd configuration, `kubeadm init`) run with `become: true`. Without passwordless sudo on cp1, local automated tasks fail.

**Q2: Why use a drop-in file (`/etc/sudoers.d/mohamed`) instead of editing `/etc/sudoers` directly?**
> **Answer:** Drop-in files ensure modularity, clear auditing, and safe automated management. Editing the primary `/etc/sudoers` directly risks syntax errors that can corrupt the configuration and lock administrators out of root access.

---

## Task 8 — Key-Based SSH from cp1 to w1

### Implementation Summary
* Generated an Ed25519 key on `cp1` under `/home/mohamed/.ssh/id_ed25519`.
* Copied public key to `w1`'s `/home/mohamed/.ssh/authorized_keys`.
* Enforced strict permissions: `chmod 700 ~/.ssh` and `chmod 600 ~/.ssh/authorized_keys`.
* Verified passwordless execution: `ssh k8slab-w1 hostname` returned `k8slab-w1`.

### Concept Questions & Answers

**Q1: Why does `ssh-copy-id` behave differently on cloud VMs vs local VMs?**
> **Answer:** Cloud VM images typically disable SSH password authentication by default, requiring public keys to be provisioned during creation via cloud-init. On local VMware VMs where password authentication is enabled initially, `ssh-copy-id` works interactively with the user's password.

**Q2: What happens if permissions on `~/.ssh` or `authorized_keys` are too loose?**
> **Answer:** OpenSSH's `StrictModes` rejects key authentication if the directory or `authorized_keys` file is writable by group or other users, silently falling back to password authentication or refusing the connection.

---

## Task 9 — Ansible Core Installation

### Implementation Summary
* Installed `ansible-core` and `git` on `cp1` via EPEL repository.
* Cloned project repository to `/home/mohamed/k8s-devops-final-project`.

### Concept Questions & Answers

**Q1: Why does w1 not require Ansible to be installed on it?**
> **Answer:** Ansible is agentless. It connects to remote nodes over standard SSH, executes transient Python modules using the node's local Python interpreter, and cleans them up upon completion. Only the controller node (`cp1`) requires Ansible.

---

## Task 10 — Inventory & Group Vars

### Implementation Summary
* Created `ansible/inventory.ini`:
  ```ini
  [k8s_master]
  cp1 ansible_connection=local

  [k8s_workers]
  w1 ansible_host=k8slab-w1 ansible_user=mohamed

  [k8s_cluster:children]
  k8s_master
  k8s_workers
  ```
* Defined global variables in `ansible/group_vars/all.yml` (`cp1_ip: 10.0.1.10`, `cluster_user: mohamed`).
* Tested connectivity with `ansible -i inventory.ini k8s_cluster -m ping -b`, confirming `SUCCESS => pong` for both nodes.

### Concept Questions & Answers

**Q1: Why is cp1 managed with `ansible_connection=local`?**
> **Answer:** Running against the local shell eliminates SSH overhead, key handling issues, and network roundtrips when the control plane executes plays against itself.

---

## Task 11 — Node Preparation Playbook

### Implementation Summary
* Created `ansible/prepare-nodes.yml`:
  * System updates (`dnf update`).
  * Administrative and networking utilities (`vim`, `curl`, `iproute`, `bind-utils`, `sysstat`, `tcpdump`).
  * Python 3 and pip installation.
  * Time synchronization via `chronyd`.
  * Conditional worker reboot when kernel updates require it.

### Concept Questions & Answers

**Q1: What does idempotency mean in Ansible playbooks?**
> **Answer:** Idempotency means executing a playbook repeatedly against the same infrastructure produces the exact same desired end state without unexpected side effects, duplicate records, or errors on subsequent runs.

---

## Task 12 — Master Playbook Orchestration (`site.yml`)

### Implementation Summary
* Created master playbook `ansible/site.yml` importing playbooks in strict sequence:
  ```yaml
  ---
  - import_playbook: prerequisites.yml
  - import_playbook: containerd.yml
  - import_playbook: kubernetes.yml
  - import_playbook: control-plane.yml
  - import_playbook: workers.yml
  ```

### Concept Questions & Answers

**Q1: Why must the control-plane playbook run before the workers playbook?**
> **Answer:** `kubeadm init` must generate cluster CA certificates, initialize the Kubernetes API server, and output an active bootstrap join token on `cp1`. Worker nodes cannot join a non-existent cluster; running out of order causes workers to time out attempting to connect to an offline control plane.

---

## Task 13 — Kubernetes Prerequisites & Container Runtime

### Implementation Summary
* `ansible/prerequisites.yml`:
  * Disabled swap immediately (`swapoff -a`) and persisted in `/etc/fstab`.
  * Set SELinux to permissive mode.
  * Loaded kernel modules (`overlay`, `br_netfilter`) and configured `/etc/modules-load.d/k8s.conf`.
  * Configured sysctl bridge parameters (`net.bridge.bridge-nf-call-iptables = 1`, `net.ipv4.ip_forward = 1`).
* `ansible/containerd.yml`:
  * Installed `containerd.io` from Docker CE repository.
  * Generated default config and configured `SystemdCgroup = true`.
  * Enabled and started `containerd` service.

### Concept Questions & Answers

**Q1: Why does kubelet refuse to run if SWAP is enabled?**
> **Answer:** `kubelet` relies on accurate memory accounting for pod scheduling and resource eviction decisions. Swap introduces unpredictable memory performance and breaks memory allocation guarantees, so Kubernetes explicitly requires it to be disabled.

**Q2: Why must containerd and kubelet share the same cgroup driver?**
> **Answer:** If they use different drivers (`cgroupfs` vs `systemd`), Linux resource limits and process hierarchies are tracked inconsistently between the two management engines, causing system instability and failed pods. Kubernetes strictly requires both to use `systemd`.

---

## Task 14 — Control Plane Initialization & CNI Setup

### Implementation Summary
* `ansible/kubernetes.yml`:
  * Configured Kubernetes official RPM repository (`v1.36`).
  * Installed `kubelet`, `kubeadm`, and `kubectl`.
  * Enabled `kubelet` service.
* `ansible/control-plane.yml`:
  * Initialized control plane:
    ```bash
    kubeadm init --pod-network-cidr=192.168.0.0/16 --apiserver-advertise-address=10.0.1.10
    ```
  * Configured user kubeconfig for `mohamed` (`~/.kube/config`).
  * Installed Calico CNI v3.31.0 manifest.
  * Captured `kubeadm token create --print-join-command` to `/tmp/join-command.sh`.

### Concept Questions & Answers

**Q1: Why is `--pod-network-cidr=192.168.0.0/16` specified during `kubeadm init`?**
> **Answer:** It defines the IP address block reserved for Pods across the cluster. Calico CNI expects `192.168.0.0/16` by default; setting this exact range during `kubeadm init` prevents IP allocation collisions and routing failures between cluster nodes and pods.

**Q2: What is the role of the CNI plugin (Calico), and what happens if it is omitted?**
> **Answer:** The Container Network Interface (CNI) configures network namespaces, assigns IP addresses to Pods, and routes traffic across nodes. If omitted, nodes remain in a `NotReady` state, CoreDNS pods cannot acquire IP addresses and stay stuck in `Pending` or `ContainerCreating`, and no application workload can schedule or communicate.

**Q3: Why does cp1 remain in `NotReady` state until Calico is applied?**
> **Answer:** Kubelet monitors the local network plugin status. Until a CNI plugin binary and network configuration are detected, kubelet reports `NetworkReady=false`, keeping the node `NotReady` to prevent scheduling pods before networking is operational.

---

## Task 15 — Worker Node Join & Cluster Verification

### Implementation Summary
* `ansible/workers.yml`:
  * Distributed `/tmp/join-command.sh` from controller to `w1`.
  * Executed cluster join idempotently using `creates: /etc/kubernetes/kubelet.conf`.
* Cluster verification via `kubectl get nodes -o wide`:
  ```
  NAME         STATUS   ROLES           AGE     VERSION   INTERNAL-IP   OS-IMAGE                      CONTAINER-RUNTIME
  k8slab-cp1   Ready    control-plane   3d19h   v1.36.5   10.0.1.10     Rocky Linux 9.8 (Blue Onyx)   containerd://2.3.6
  k8slab-w1    Ready    <none>          3d18h   v1.36.5   10.0.1.11     Rocky Linux 9.8 (Blue Onyx)   containerd://2.3.6
  ```
* All system pods in `kube-system` (`calico-node`, `coredns`, `etcd`, `kube-apiserver`) verified `1/1 Running`.

---

## Task 16 — Task Tracker Microservice & Unit Testing

### Implementation Summary
* **Architecture:** Flask microservice utilizing SQLAlchemy ORM supporting both SQLite (local development/unit testing) and PostgreSQL (production/Kubernetes).
* **Core Feature:** Implemented dynamic `priority` field (`low`, `medium`, `high`, default `medium`) across models, RESTful APIs, and the UI layer.
* **Frontend:** Apple-inspired minimalist Claymorphism UI with clean typography, balanced shadows, mobile responsiveness, and interactive state management.
* **Quality Assurance:** 5 automated unit tests implemented with `pytest` in `app/test_app.py`:
  * `test_create_task_default_priority`: Verifies fallback to `medium`.
  * `test_create_task_with_explicit_priority`: Verifies explicit priority storage.
  * `test_create_task_rejects_invalid_priority`: Verifies HTTP 400 rejection for invalid values.
  * `test_list_tasks`: Verifies JSON listing output.
  * `test_update_task_priority`: Verifies PUT update mechanism.
* **Seed Script:** Implemented `app/scripts/seed.py` inserting sample tasks across all priority tiers.

---

## Task 17 — Production Dockerfile & Docker Compose

### Implementation Summary
* **Dockerfile (`app/Dockerfile`):**
  * Base: `python:3.12-slim` for minimal footprint and reduced CVE profile.
  * Layer caching: Dependencies installed before application source copy.
  * Security Context: Runs as unprivileged service user `appuser` (UID 10001).
  * Production WSGI: `gunicorn` serving on port 5000.
* **docker-compose.yml:**
  * `db` service: PostgreSQL 16 Alpine, named volume `db_data`, healthcheck via `pg_isready`.
  * `web` service: Built from `app/`, depends on `db` being healthy.
* **Verification:** Tested `/health` and `/ready` endpoints returning HTTP 200. Persisted task entries across `docker compose restart db`, confirming named volume retention.

### Concept Questions & Answers

**Q1: What is the advantage of using a `slim` Python base image compared to a standard image?**
> **Answer:** A slim image strips out build tools, documentation, and extra system libraries not needed at runtime, resulting in a smaller attack surface, fewer CVEs to patch, and significantly faster image pulls/builds in CI/CD pipelines.

**Q2: What is the operational difference between the `/health` and `/ready` endpoints?**
> **Answer:** `/health` only confirms the process itself is alive and responding (liveness) and never touches external dependencies, so a monitoring system can restart a truly hung container. `/ready` additionally executes a lightweight query against PostgreSQL, confirming the app can serve real traffic only once its database dependency is reachable (readiness) — this is what should gate traffic routing in Kubernetes.

> **Port Mapping Note:** Host port 5050 is mapped to container port 5000 (`5050:5000`) due to Windows Hyper-V / WinNAT reserving port 5000 on the local host. All application endpoints are accessible via `http://localhost:5050`.

---

## Task 20 — Engineering Post-Mortems

### Post-Mortem 1: Worker Join Script Never Reached `w1` (`workers.yml`)
* **Error:** The reference `workers.yml` playbook fetched `/tmp/join-command.sh` with `delegate_to: cp1` and then ran `bash /tmp/join-command.sh` on `w1`. During execution, `w1` failed with `bash: /tmp/join-command.sh: No such file or directory`.
* **Cause:** `fetch` copies a file from the delegated host to the Ansible controller. Because the controller is `cp1` itself, the fetched join script remained on `cp1` and was never transmitted to `w1`, where the `shell` task runs.
* **Fix:** Retained the `fetch` task and added a `copy` task that transfers `/tmp/join-command.sh` from the controller to `w1` (mode `0755`) prior to running the join command. Applied `args: { creates: /etc/kubernetes/kubelet.conf }` to ensure idempotency.

### Post-Mortem 2: Windows WinNAT / Hyper-V Port 5000 Collision
* **Error:** Running `docker compose up -d` on the Windows host failed with `bind: An attempt was made to access a socket in a way forbidden by its access permissions` when binding port 5000.
* **Cause:** Windows Hyper-V and WinNAT dynamically reserve broad ranges of ephemeral TCP ports, including port 5000, preventing Docker Desktop from binding to `0.0.0.0:5000`.
* **Fix:** Updated `docker-compose.yml` to map host port 5050 to container port 5000 (`5050:5000`). Kept internal container networking on standard port 5000, enabling uninterrupted local browser testing at `http://localhost:5050`.

### Post-Mortem 3: Workstation Reboot Network Lockout by VPN WFP Driver
* **Error:** Following workstation restart, pinging and SSH access from the laptop to `k8slab-cp1` (`10.0.1.10`) failed with `General failure (status 11050)` and socket `Permission denied`.
* **Cause:** Proton VPN service resumed on Windows boot and activated its Windows Filtering Platform (WFP) firewall filter, blocking non-tunneled outgoing packets to the private VMware NAT subnet (`10.0.1.0/24`).
* **Fix:** Allowed local area network (LAN) traffic in VPN split-tunneling settings, instantly restoring bi-directional IP and SSH connectivity between the workstation host and the VMware VMnet8 virtual network adapter (`10.0.1.1`).
