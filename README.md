# k8s-devops-final-project

## Task 13 — Kubernetes Prerequisites & Container Runtime

### Concept Questions & Answers

**Q1: Why does kubelet refuse to run if SWAP is enabled?**
> **Answer:** `kubelet` relies on accurate memory accounting for pod scheduling and resource eviction decisions. Swap introduces unpredictable memory performance and breaks memory allocation guarantees, so Kubernetes explicitly requires it to be disabled.

**Q2: Why must containerd and kubelet share the same cgroup driver?**
> **Answer:** If they use different drivers (`cgroupfs` vs `systemd`), Linux resource limits and process hierarchies are tracked inconsistently between the two management engines, causing system instability and failed pods. Kubernetes strictly requires both to use `systemd`.

## Task 14 — Control Plane Initialization & CNI Setup

### Concept Questions & Answers

**Q1: Why is `--pod-network-cidr=192.168.0.0/16` specified during `kubeadm init`?**
> **Answer:** It defines the IP address block reserved for Pods across the cluster. Calico CNI expects `192.168.0.0/16` by default; setting this exact range during `kubeadm init` prevents IP allocation collisions and routing failures between cluster nodes and pods.

**Q2: What is the role of the CNI plugin (Calico), and what happens if it is omitted?**
> **Answer:** The Container Network Interface (CNI) configures network namespaces, assigns IP addresses to Pods, and routes traffic across nodes. If omitted, nodes remain in a `NotReady` state, CoreDNS pods cannot acquire IP addresses and stay stuck in `Pending` or `ContainerCreating`, and no application workload can schedule or communicate.

## Task 15 — Worker Node Join & Cluster Verification

### Concept Questions & Answers

**Q1: Why must the control-plane playbook run before the workers playbook?**
> **Answer:** `kubeadm init` must generate the cluster CA certificates, initialize the Kubernetes API server, and produce an active bootstrap token on the control plane first. A worker node cannot join a non-existent cluster; executing the playbooks out of order causes the worker's join process to time out while attempting to connect to an offline API server.

## Task 20 — Engineering Post-Mortems

### Post-Mortem: Worker join script never reaches `w1` (`workers.yml`)

* **Error:** The reference `workers.yml` fetched `/tmp/join-command.sh` with `delegate_to: cp1` and then ran `bash /tmp/join-command.sh` on `w1`. Caught during code review before execution: on `w1` this would fail with `bash: /tmp/join-command.sh: No such file or directory`.
* **Cause:** `fetch` copies a file from the delegated host to the Ansible controller. Here the controller is `cp1` itself, so the file stays on `cp1` and is never placed on `w1`, where the `shell` task runs.
* **Fix:** Kept the `fetch` task and added a `copy` task that pushes the file from the controller to `w1` (`/tmp/join-command.sh`, mode 0755) before `shell: bash /tmp/join-command.sh`. The `creates: /etc/kubernetes/kubelet.conf` guard keeps the join idempotent. The second `site.yml` run confirmed it: `Join cluster` returned `ok` (skipped by the guard) and both nodes stayed `Ready`.

## Task 16 — Task Tracker Microservice & Unit Testing

### Implementation Summary
- **Architecture**: Flask microservice utilizing SQLAlchemy ORM supporting both SQLite (local development) and PostgreSQL (production/Kubernetes).
- **Core Feature**: Implemented dynamic `priority` field (`low`, `medium`, `high`) across backend models, RESTful APIs, and the UI layer.
- **Frontend**: Designed an Apple-inspired minimalist Claymorphism UI with clean typography, balanced shadows, full mobile responsiveness, and interactive state management.
- **Quality Assurance**: 5 automated unit tests implemented with `pytest` verifying health checks, default priority fallback, explicit priority setting, and input validation.
- **Containerization**: Standardized `Dockerfile` built on `python:3.11-slim`, running with an unprivileged service user (`appuser` UID 10001) for strict Kubernetes security context compliance.

## Task 17 — Production Dockerfile & Docker Compose

### Implementation Summary
- **Dockerfile**: `python:3.12-slim` base, `APP_VERSION` build arg, layer-cached dependency install, non-root `appuser` (UID 10001), `gunicorn` on port 5000.
- **docker-compose.yml**: `db` service (PostgreSQL 16, named volume `db_data`, healthcheck via `pg_isready`) and `web` service (built from `app/`, waits for `db` to be healthy).
- **Verification**: `docker compose up -d --build` brought both services to `Up`/`Up (healthy)`. `/health` and `/ready` endpoints returned 200 with valid JSON. Tasks created via the UI/API persisted across `docker compose restart db`, confirming the named volume correctly preserves PostgreSQL data independent of container lifecycle.

### Concept Questions & Answers

**Q1: What is the advantage of using a `slim` Python base image compared to a standard image?**
> **Answer:** A slim image strips out build tools, documentation, and extra system libraries not needed at runtime, resulting in a smaller attack surface, fewer CVEs to patch, and significantly faster image pulls/builds in CI/CD pipelines.

**Q2: What is the operational difference between the `/health` and `/ready` endpoints?**
> **Answer:** `/health` only confirms the process itself is alive and responding (liveness) and never touches external dependencies, so a monitoring system can restart a truly hung container. `/ready` additionally executes a lightweight query against PostgreSQL, confirming the app can serve real traffic only once its database dependency is reachable (readiness) — this is what should gate traffic routing in Kubernetes.

> **Port Mapping Note:** Host port 5050 is mapped to container port 5000 (`5050:5000`) due to Windows Hyper-V / WinNAT reserving port 5000 on the local host. All application endpoints are accessible via `http://localhost:5050`.
