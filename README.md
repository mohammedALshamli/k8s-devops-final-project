# k8s-devops-final-project

DevOps Bootcamp Final Capstone — Path B (VMware Workstation)  
**Author:** Mohammed Alshamli  
**Cluster Architecture:** Multi-Node Kubernetes Cluster on Rocky Linux 9 (VMware NAT `10.0.1.0/24`)

---

## Architecture & Cluster Specifications

| Hostname | Role | IP Address | vCPU | RAM | Disk | OS | Container Runtime | Kubernetes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `k8slab-cp1` | Control Plane & Controller | `10.0.1.10` | 2 | 4 GB | 40 GB | Rocky Linux 9.8 | containerd 2.3.6 (systemd) | v1.36.5 |
| `k8slab-w1` | Worker Node 1 | `10.0.1.11` | 2 | 4 GB | 40 GB | Rocky Linux 9.8 | containerd 2.3.6 (systemd) | v1.36.5 |
| `k8slab-w2` | Worker Node 2 (Bonus 1) | `10.0.1.12` | 2 | 4 GB | 40 GB | Rocky Linux 9.8 | containerd 2.3.6 (systemd) | v1.36.5 |

* **Network Topology:** VMware NAT (`VMnet8`), Gateway: `10.0.1.2`, Host Interface: `10.0.1.1`
* **Pod Network CIDR:** `192.168.0.0/16` (Calico CNI v3.31.0)
* **Automation User:** `mohamed` (passwordless sudo, key-based SSH authentication)

---

## Quick Reproduction Commands

### 1. Repository Setup & Workstation Tooling
```bash
# Clone the repository
git clone https://github.com/mohammedALshamli/k8s-devops-final-project.git
cd k8s-devops-final-project

# Verify local tooling
git --version
ssh -V
python --version
terraform -version
kubectl version --client
```

### 2. Node Access via SSH
```bash
# SSH into Control Plane
ssh -i ~/.ssh/k8slab_key ouda@10.0.1.10

# SSH into Worker Nodes
ssh -i ~/.ssh/k8slab_key ouda@10.0.1.11
ssh -i ~/.ssh/k8slab_key ouda@10.0.1.12
```

### 3. Terraform Validation (Task 5)
```bash
cd terraform
terraform fmt -check
terraform init -backend=false
terraform validate
cd ..
```

### 4. Cluster Automation via Ansible (Tasks 10–15 & Bonus 1)
```bash
# Executed on cp1 (as user mohamed):
cd /home/mohamed/k8s-devops-final-project/ansible

# Test connectivity across all nodes
ansible -i inventory.ini k8s_cluster -m ping -b

# Full cluster deployment
ansible-playbook -i inventory.ini site.yml

# Scale out additional worker node (Bonus 1)
ansible-playbook -i inventory.ini workers.yml --limit w2
```

### 5. Verify Cluster & Deploy Workloads (Tasks 15, 19 & Bonus 2)
```bash
# Remote administration directly from laptop workstation (Bonus 2)
kubectl get nodes -o wide
kubectl get pods -A -o wide

# Deploy production manifests
kubectl apply -f k8s/

# Verify application deployment and persistent storage
kubectl get pods,svc,pvc -o wide
curl http://10.0.1.10:30080/ready
curl http://10.0.1.11:30080/ready
curl http://10.0.1.12:30080/ready
```

### 6. Local Testing with Docker Compose (Task 17)
```powershell
# In project root on workstation host:
docker compose up -d --build

# Verify endpoints (mapped to 5050 due to Windows WinNAT ephemeral exclusion)
curl http://localhost:5050/health
curl http://localhost:5050/ready

# Run unit tests
python -m pytest app/ -v
```

---

## Task 1 — Project Repository & Git Hygiene

### Implementation Summary
* Initialized modular directory structure: `terraform/`, `ansible/`, `app/`, `k8s/`, `docs/screenshots/`.
* Configured `.gitignore` to prevent credential leakage, cloud state exposure, and binary artifacts.
* Enforced semantic commit messaging standards (`feat`, `fix`, `chore`, `docs`).

### Concept Questions & Answers

**Q1: Which files/directories are excluded by `.gitignore` and why?**
> **Answer:** 
> * `*.tfstate*`: Prevents exposing cloud infrastructure resource IDs, private IPs, and plaintext attributes.
> * `.terraform/`: Local provider plugins and binary cache automatically restored via `terraform init`.
> * `terraform.tfvars`: Contains deployment-specific variables, subscription IDs, and environment secrets.
> * `*.pem`, `id_ed25519*`, `k8slab_key*`: Private SSH keys that must never leave the local environment.
> * `kubeconfig`, `admin.conf`: Cluster administrative tokens; leaking them grants full cluster compromise.
> * `app/instance/*.db`, `app/__pycache__/`, `app/.pytest_cache/`: Local runtime SQLite files and Python bytecode caches.

**Q2: If a secret is accidentally committed and later deleted in a subsequent commit, is it safe?**
> **Answer:** No. Git functions as an immutable, append-only Directed Acyclic Graph (DAG). Deleting a file in a later commit only records a new state at `HEAD`; the file blob remains accessible throughout the commit history, tree objects, and reflog. Any cloned repository can check out that historical revision. Compromised credentials must be revoked and rotated immediately.

---

## Task 2 — Workstation Tool Verification

### Implementation Summary
Verified required tool versions on the host machine:
* `git` version 2.45+
* `OpenSSH` (ssh client)
* `python` 3.12+
* `terraform` v1.9+
* `kubectl` v1.30+
* `VMware Workstation Pro` 17

---

## Task 3 — Cloud Account Setup [SKIPPED]

### Implementation Summary
* **Status:** Skipped (Azure-only, Path A).
* **Rationale:** This project follows **Path B (VMware Workstation)**, running fully self-contained on local hypervisor virtual machines to avoid recurring cloud infrastructure costs and cloud API rate limits.

---

## Task 4 — SSH Key Pair Generation

### Implementation Summary
* Generated a dedicated Ed25519 SSH keypair on the workstation host:
  ```bash
  ssh-keygen -t ed25519 -f ~/.ssh/k8slab_key -C "k8slab"
  ```
* Provisioned the public key (`k8slab_key.pub`) onto cluster virtual machines (`cp1`, `w1`, `w2`).

### Concept Questions & Answers

**Q1: What is the security difference between the private key and public key?**
> **Answer:** The public key (`.pub`) is an asymmetric derivation placed in `~/.ssh/authorized_keys` on target hosts to verify cryptographic signatures. The private key proves identity, must remain on the client machine with restricted permissions (`chmod 600`), and is never transmitted over the network.

---

## Task 5 — Terraform Code (Write & Validate)

### Implementation Summary
* Authored declarative IaC definitions in `terraform/`:
  * `providers.tf`: Provider declarations pinned to `hashicorp/azurerm ~> 4.0`.
  * `variables.tf`: Schema definitions for network ranges, resource groups, and node specs.
  * `network.tf`: Virtual network (`10.0.0.0/16`), subnet (`10.0.1.0/24`), and NSG rules.
  * `vms.tf`: VM resources mapped with fixed private IPs (`10.0.1.10`, `10.0.1.11`).
  * `cloud-init.tftpl`: Bootstrap cloud-init template for automated user configuration.
  * `outputs.tf`: Exported private IP and connection parameters.
* Validated syntax: `terraform fmt -check` and `terraform validate` passed with zero errors.

### Concept Questions & Answers

**Q1: Why does the Network Security Group (NSG) not need explicit rules for cp1 ↔ w1 internal traffic?**
> **Answer:** Cloud and virtual network topologies permit all traffic within the same virtual network/subnet boundary by default. NSG security rules act as edge packet filters to govern ingress and egress across the external perimeter.

**Q2: Why must private IPs assigned to Kubernetes nodes be static?**
> **Answer:** Kubernetes control plane certificates (SANs), etcd cluster peer topologies, kubelet API registrations, and bootstrap join tokens are permanently bound to node IP addresses. Dynamic IP changes break certificate validation, cause etcd quorum loss, and disconnect worker nodes.

**Q3: What information is stored in `terraform.tfstate`?**
> **Answer:** The state file holds a complete mapping of declared resources to physical infrastructure identifiers, IP allocations, dependency graphs, and all configuration inputs in unencrypted plaintext.

---

## Task 6B — VMware Workstation Infrastructure Alternative

### Implementation Summary
* Deployed Rocky Linux 9 virtual machines on VMware Workstation:
  * `k8slab-cp1`: 2 vCPU, 4 GB RAM, 40 GB disk, IP `10.0.1.10`
  * `k8slab-w1`: 2 vCPU, 4 GB RAM, 40 GB disk, IP `10.0.1.11`
  * `k8slab-w2`: 2 vCPU, 4 GB RAM, 40 GB disk, IP `10.0.1.12` (Bonus 1)
* Configured VMware NAT network (`VMnet8`, `10.0.1.0/24`, Gateway: `10.0.1.2`).
* Enforced static IP configurations via `nmcli` and populated `/etc/hosts` across all nodes.
* Verified bidirectional reachability (0% packet loss). Documented in `docs/vm-specs.md`.

---

## Task 7 — Automation User Setup

### Implementation Summary
* Configured dedicated automation user `mohamed` with passwordless sudo:
  ```bash
  sudo useradd -m -G wheel mohamed
  echo "mohamed ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/mohamed
  sudo chmod 0440 /etc/sudoers.d/mohamed
  sudo visudo -c
  ```

### Concept Questions & Answers

**Q1: Why does cp1 need passwordless sudo if it is already the Ansible controller?**
> **Answer:** `cp1` executes plays against itself via `ansible_connection=local`. System operations (`dnf`, kernel parameters, containerd runtime configuration, `kubeadm init`) run under `become: true`. Without passwordless sudo on `cp1`, non-interactive local automation fails.

**Q2: Why use a drop-in file (`/etc/sudoers.d/mohamed`) instead of editing `/etc/sudoers` directly?**
> **Answer:** Drop-in files ensure modularity and clean package management. Package updates will not overwrite custom permissions, and isolated configuration files can be added or deleted programmatically without risking syntax errors in the core `/etc/sudoers` file.

---

## Task 8 — Key-Based SSH from cp1 to w1

### Implementation Summary
* Generated an Ed25519 key on `cp1` (`/home/mohamed/.ssh/id_ed25519`).
* Installed the public key into `w1`'s `/home/mohamed/.ssh/authorized_keys`.
* Enforced strict directory permissions: `chmod 700 ~/.ssh` and `chmod 600 ~/.ssh/authorized_keys`.
* Verified non-interactive execution: `ssh k8slab-w1 hostname` returned `k8slab-w1`.

### Concept Questions & Answers

**Q1: Why does `ssh-copy-id` behave differently on cloud VMs vs local VMs?**
> **Answer:** Cloud VM images typically disable password-based SSH authentication out of the box, requiring public keys to be injected at creation time via cloud-init. Local virtualization installations retain password authentication by default, allowing interactive `ssh-copy-id` bootstrapping.

**Q2: What happens if permissions on `~/.ssh` or `authorized_keys` are too loose?**
> **Answer:** OpenSSH's `StrictModes` security check aborts key authentication if the `.ssh` directory or `authorized_keys` file is writable by group or world (`g+w` or `o+w`). OpenSSH falls back to password authentication or rejects the session entirely.

---

## Task 9 — Ansible Core Installation

### Implementation Summary
* Installed `ansible-core` and `git` on `cp1` via EPEL repositories.
* Cloned project repository to `/home/mohamed/k8s-devops-final-project`.

### Concept Questions & Answers

**Q1: Why does w1 not require Ansible to be installed on it?**
> **Answer:** Ansible operates agentlessly. The control plane connects over standard OpenSSH, executes transient Python scripts using the target machine's system interpreter, and removes the payload immediately after execution.

---

## Task 10 — Inventory & Group Vars

### Implementation Summary
* Created `ansible/inventory.ini`:
  ```ini
  [k8s_master]
  cp1 ansible_connection=local

  [k8s_workers]
  w1 ansible_host=k8slab-w1 ansible_user=mohamed
  w2 ansible_host=k8slab-w2 ansible_user=mohamed

  [k8s_cluster:children]
  k8s_master
  k8s_workers
  ```
* Defined environment parameters in `ansible/group_vars/all.yml` (`cp1_ip: 10.0.1.10`, `pod_network_cidr: "192.168.0.0/16"`).
* Validated execution: `ansible -i inventory.ini k8s_cluster -m ping -b` returned `SUCCESS => pong` across all hosts.

### Concept Questions & Answers

**Q1: Why is cp1 managed with `ansible_connection=local`?**
> **Answer:** Running plays locally bypasses network latency, SSH daemon handshakes, and key verification overhead when the control plane executes automation against itself.

---

## Task 11 — Node Preparation Playbook

### Implementation Summary
* Authored `ansible/prepare-nodes.yml`:
  * System package updates (`dnf update`).
  * Installed utilities (`vim`, `curl`, `iproute`, `bind-utils`, `sysstat`, `tcpdump`, `python3-pip`).
  * Time synchronization configured using `chronyd`.
  * Conditional worker reboot triggers on kernel upgrades.

### Concept Questions & Answers

**Q1: What does idempotency mean in Ansible playbooks?**
> **Answer:** An idempotent task brings the target system to the declared end state regardless of starting conditions, making zero modifications and producing zero side effects if the system already matches the declared configuration.

---

## Task 12 — Master Playbook Orchestration (`site.yml`)

### Implementation Summary
* Implemented master orchestration in `ansible/site.yml`:
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
> **Answer:** `kubeadm init` initializes the cluster CA certificates, starts the API server and etcd quorum, and registers the initial bootstrap token. Worker nodes require an active API server endpoint to authenticate and fetch cluster info; running workers beforehand causes join timeouts.

---

## Task 13 — Kubernetes Prerequisites & Container Runtime

### Implementation Summary
* `ansible/prerequisites.yml`:
  * Disabled swap (`swapoff -a`) and removed swap mounts from `/etc/fstab`.
  * Set SELinux to permissive mode.
  * Loaded kernel modules `overlay` and `br_netfilter` via `/etc/modules-load.d/k8s.conf`.
  * Enabled bridging sysctl flags (`net.bridge.bridge-nf-call-iptables = 1`, `net.ipv4.ip_forward = 1`).
* `ansible/containerd.yml`:
  * Installed `containerd.io` from Docker CE repository.
  * Generated default configuration with `SystemdCgroup = true`.
  * Enabled and started `containerd.service`.

### Concept Questions & Answers

**Q1: Why does kubelet refuse to run if SWAP is enabled?**
> **Answer:** Kubelet assumes complete determinism over node memory allocation and cgroup resource tracking. Paging pod memory to disk causes unpredictable latency, invalidates quality-of-service (QoS) guarantees, and degrades container health checks.

**Q2: Why must containerd and kubelet share the same cgroup driver?**
> **Answer:** If containerd uses `cgroupfs` while kubelet uses `systemd`, the operating system maintains two competing process hierarchies for resource tracking. Under memory pressure, systemd fails to enforce container limits correctly, leading to host instability and terminated pods.

---

## Task 14 — Control Plane Initialization & CNI Setup

### Implementation Summary
* Installed `kubelet`, `kubeadm`, and `kubectl` pinned to v1.36.
* Executed cluster bootstrap:
  ```bash
  kubeadm init --pod-network-cidr=192.168.0.0/16 --apiserver-advertise-address=10.0.1.10
  ```
* Configured local `~/.kube/config` and deployed Calico CNI v3.31.0.
* Captured node join command to `/tmp/join-command.sh`.

### Concept Questions & Answers

**Q1: Why is `--pod-network-cidr=192.168.0.0/16` specified during `kubeadm init`?**
> **Answer:** It defines the IP address block reserved for Pods across the cluster. Calico CNI defaults to `192.168.0.0/16`. Matching this CIDR ensures that kube-controller-manager and Calico IPAM allocate non-overlapping, routable pod subnets.

**Q2: What is the role of the CNI plugin (Calico), and what happens if it is omitted?**
> **Answer:** The CNI sets up virtual network interfaces (veth pairs), provisions IP addresses, and configures routing between nodes. Without a CNI, the node condition remains `NetworkPluginNotReady`, CoreDNS cannot bind an IP, and all pods remain stuck in `Pending`.

**Q3: Why does cp1 remain in `NotReady` state until Calico is applied?**
> **Answer:** Kubelet periodically queries the local CNI configuration in `/etc/cni/net.d`. Until a valid CNI configuration is found and the network loopback/bridge is initialized, kubelet reports `Ready=False` to prevent scheduling workloads on an unrouted node.

---

## Task 15 — Worker Node Join & Cluster Verification

### Implementation Summary
* Automated worker joins in `ansible/workers.yml` using `creates: /etc/kubernetes/kubelet.conf` for idempotency.
* Verified cluster status using `kubectl get nodes -o wide`:
  ```
  NAME         STATUS   ROLES           AGE    VERSION   INTERNAL-IP   OS-IMAGE                      CONTAINER-RUNTIME
  k8slab-cp1   Ready    control-plane   6d4h   v1.36.5   10.0.1.10     Rocky Linux 9.8 (Blue Onyx)   containerd://2.3.6
  k8slab-w1    Ready    <none>          6d3h   v1.36.5   10.0.1.11     Rocky Linux 9.8 (Blue Onyx)   containerd://2.3.6
  k8slab-w2    Ready    <none>          3h     v1.36.5   10.0.1.12     Rocky Linux 9.8 (Blue Onyx)   containerd://2.3.6
  ```
* Verified all system pods in `kube-system` (`calico-node`, `coredns`, `kube-proxy`, `etcd`, `kube-apiserver`) in `Running` state.

---

## Task 16 — Task Tracker Microservice & Unit Testing

### Implementation Summary
* **Architecture:** Flask REST API with SQLAlchemy ORM supporting SQLite (unit tests) and PostgreSQL (production).
* **Core Features:** Dynamic task priority classification (`low`, `medium`, `high`, default `medium`) across models and REST endpoints.
* **Frontend:** Responsive, modern Claymorphic UI with clean hierarchy and micro-animations.
* **Unit Testing:** 5 automated tests in `app/test_app.py` covering default priority assignment, explicit priority persistence, invalid priority rejection (HTTP 400), task retrieval, and update flows.
* **Database Seeding:** Implemented `app/scripts/seed.py` for testing and demonstration datasets.

---

## Task 17 — Production Dockerfile & Docker Compose

### Implementation Summary
* **Dockerfile (`app/Dockerfile`):**
  * Base: `python:3.12-slim` for minimal image size and vulnerability surface.
  * Layer caching: Installed `requirements.txt` prior to copying application source.
  * Security Context: Runs as unprivileged service user `appuser` (UID 10001).
  * Production WSGI: `gunicorn` serving on port 5000.
* **docker-compose.yml:**
  * `db` service: PostgreSQL 16 Alpine, named volume `db_data`, native healthcheck via `pg_isready`.
  * `web` service: Built from `app/`, gated by PostgreSQL dependency readiness.
  * Mapped host port 5050 to container port 5000 (`5050:5000`) to avoid Windows WinNAT dynamic port reservation collisions.
* **Verification:** Confirmed HTTP 200 on `/health` and `/ready`. Validated data persistence across `docker compose restart db`.

### Concept Questions & Answers

**Q1: What is the advantage of using a `slim` Python base image compared to a standard image?**
> **Answer:** Slim images omit compilers, package managers, and development header files unnecessary at runtime. This results in faster image transfer speeds across CI/CD runners, lower attack surfaces, and fewer upstream CVEs to remediate.

**Q2: What is the operational difference between the `/health` and `/ready` endpoints?**
> **Answer:** `/health` (Liveness) only checks that the Python process and WSGI workers are responsive without checking external dependencies, allowing orchestrators to restart deadlocked processes. `/ready` (Readiness) verifies upstream database connectivity, preventing traffic routing to the container until it can complete transactions.

---

## Task 18 — GitHub Actions CI/CD Pipeline

### Implementation Summary
* **Workflow Configuration:** Created `.github/workflows/ci-cd.yml` triggered on push and pull-request events targeting `main`.
* **Pipeline Jobs:**
  1. `lint-and-test`: Python 3.12 environment running style enforcement via `flake8` and unit testing via `pytest`.
  2. `terraform-validate`: Validates IaC syntax with `terraform fmt -check` and `terraform validate`.
  3. `build-and-push`: Multi-stage build leveraging Docker Buildx, authenticated to GitHub Container Registry (GHCR) using dynamic `${{ secrets.GITHUB_TOKEN }}`. Pushes both `latest` and git commit SHA tags.
* **Registry Artifact:** Published container image to `ghcr.io/mohammedalshamli/k8s-devops-final-project:latest`.

### Technical Questions & Answers

**Q1: Why separate linting and testing from the Docker image build into distinct pipeline jobs?**
> **Answer:** Enforces the "Fail-Fast" principle. Linting and unit tests complete in seconds. Failing early stops the pipeline before executing resource-intensive container builds, conserving CI/CD runner compute hours and preventing flawed code from producing images.

**Q2: What is the security advantage of publishing to GHCR using `${{ secrets.GITHUB_TOKEN }}` over Docker Hub with static credentials?**
> **Answer:** The default `GITHUB_TOKEN` is dynamically generated, scoped exclusively to the executing repository, and automatically revoked once the job concludes. This removes the risk of leaking permanent credentials, personal access tokens, or static passwords.

---

## Task 19 — Kubernetes Production Deployment

### Implementation Summary
* **Kubernetes Manifest Architecture (`k8s/`):**
  * `postgres-secret.yaml`: Secure credential storage for database passwords and connection strings.
  * `postgres-pvc.yaml`: PersistentVolumeClaim requesting 2Gi storage dynamically bound to `postgres-pv`.
  * `postgres-deployment.yaml`: Single-replica database with init-containers managing mount permissions and `pg_isready` readiness probes.
  * `postgres-service.yaml`: Internal `ClusterIP` exposing port 5432.
  * `app-deployment.yaml`: Production application pulling from GHCR, secured with liveness (`/health`) and readiness (`/ready`) probes.
  * `app-service.yaml`: `NodePort` service exposing the application externally across nodes on port `30080`.
* **Verification:** Confirmed both pods running `1/1`. Verified external service availability returning `{"status":"ready"}` across all node IPs (`10.0.1.10:30080`, `10.0.1.11:30080`, `10.0.1.12:30080`).

### Technical Questions & Answers

**Q1: What is the operational difference between a `ClusterIP` and a `NodePort` service?**
> **Answer:** A `ClusterIP` exposes the service on an internal-only IP accessible exclusively from within the cluster, which is ideal for securing backing databases. A `NodePort` exposes the service on a dedicated high-range port (30000–32767) across the external IP of every node, allowing outside clients to route directly to application pods.

**Q2: Why mount storage using a `PersistentVolumeClaim` (PVC) instead of direct `hostPath` mounts in the Deployment spec?**
> **Answer:** PVCs decouple application pod manifests from node-level storage implementations. If pods are rescheduled or upgraded across different nodes, orchestrators re-bind the claim without modifying application definitions.

---

## Task 20 — Project Documentation & Engineering Post-Mortems

### Post-Mortem 1: SCP Infinite Recursion — Maximum Directory Depth Exceeded
* **Error:** `scp: Maximum directory depth exceeded: 64 levels`
* **Root Cause:** Running `scp -r ouda@10.0.1.10:~/k8s-devops-final-project/k8s .` while already inside `k8slab-cp1` created a self-referential SSH loop, copying `k8s/` recursively into itself until hitting OpenSSH's limit of 64 nested levels.
* **Fix:** Purged the recursive tree (`rm -rf k8s/k8s`) and established strict execution isolation: file transfers from the host run only within the host PowerShell shell, never within the guest SSH terminal.

---

### Post-Mortem 2: Host Network Lockout & WinNAT Port Collisions
* **Error:** `bind: An attempt was made to access a socket in a way forbidden by its access permissions` on port 5000, combined with host-to-guest ICMP drops (`General failure 11050`).
* **Root Cause:** Windows Hyper-V and WinNAT reserved dynamic port ranges overlapping port 5000. Additionally, the host VPN Windows Filtering Platform (WFP) driver blocked outgoing non-tunneled traffic to the VMware NAT subnet (`10.0.1.0/24`).
* **Fix:** Remapped host port 5050 to container port 5000 (`5050:5000`) in `docker-compose.yml`, and configured split-tunneling LAN rules in the host VPN client, restoring bidirectional communication to `VMnet8`.

---

### Post-Mortem 3: SQLAlchemy Database Driver Mismatch (`psycopg` vs `psycopg2-binary`)
* **Error:** `ModuleNotFoundError: No module named 'psycopg'` / `[ERROR] Worker failed to boot.`
* **Root Cause:** SQLAlchemy 2.0 interprets unqualified `postgresql://` URIs by attempting to import the `psycopg` (v3) driver, whereas the project installed `psycopg2-binary`.
* **Fix:** Updated `DATABASE_URL` to explicitly declare the installed driver: `postgresql+psycopg2://taskuser:taskpass@db:5432/taskdb`.

---

### Incident Log: Additional Edge Cases Resolved
* **Ansible Join Script File Delegation:** `workers.yml` originally fetched the join command to the controller but lacked a distribution task to transfer it to workers; resolved by adding an explicit `copy` task with `0755` permissions and `creates: /etc/kubernetes/kubelet.conf`.
* **Interface IP Configuration Recovery:** An inadvertent `nmcli` command modified `cp1`'s interface to a conflicting IP, deactivating the connection. The IP was reassigned to `10.0.1.10/24` via direct VMware console access, restoring cluster connectivity.
* **cgroups v2 Systemd Integration:** Aligned containerd configuration with `SystemdCgroup = true` to match kubelet's systemd cgroup driver, eliminating node-level pod sandbox drops.

---

## Task 21 — Teardown & Environment Decommissioning [VMware]

### Implementation Summary
* **Decommissioning Process:**
  * For Path B on VMware Workstation, there is zero risk of cloud billing or unexpected metered charges.
  * Executed graceful host shutdown across all cluster nodes:
    ```bash
    # Executed on cp1, w1, and w2
    sudo shutdown -h now
    ```
  * Verified all virtual machine instances (`k8slab-cp1`, `k8slab-w1`, `k8slab-w2`) reached `Powered Off` state in VMware Workstation.
* **Artifact Reference:** Teardown verification screenshot captured and saved to [`docs/screenshots/task21-vms-powered-off.png`](file:///docs/screenshots/task21-vms-powered-off.png).

---

## Bonus Objectives (Completed)

### Bonus 1: Multi-Node Cluster Scaling via Ansible (`k8slab-w2`)
* Added worker node `w2` (`10.0.1.12`) to the `[k8s_workers]` group in `ansible/inventory.ini`.
* Executed targeted worker playbook:
  ```bash
  ansible-playbook -i inventory.ini workers.yml --limit w2
  ```
* Verified node successfully joined and transitioned to `Ready` state with containerd v2.3.6 and Calico networking:
  ```
  k8slab-w2   Ready   <none>   3h   v1.36.5   10.0.1.12   Rocky Linux 9.8 (Blue Onyx)   containerd://2.3.6
  ```

### Bonus 2: Remote Workstation Administration via `kubectl`
* Exported `/etc/kubernetes/admin.conf` from `k8slab-cp1` to the host laptop workstation (`~/.kube/config`).
* Maintained control plane endpoint at `https://10.0.1.10:6443`.
* Verified direct management from Windows PowerShell without active SSH sessions:
  ```powershell
  kubectl get nodes -o wide
  kubectl get pods,svc,pvc -o wide
  ```
