# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-08-07

### Added

- **Core Engine**: `scripts/prompt.py` implemented to compile, validate, and export prompts.
- **Schema**: `profile.schema.json` to enforce strict validation on profile configurations.
- **Environment**: Integrated `uv` for lightning-fast, deterministic Python environments (Python 3.12).
- **System Policies**: Added base engineering rules, response formats, and safety rules.
- **Roles**: Created personas for `java-architect`, `devops-engineer`, `cloud-native-engineer`, and `security-expert`.
- **Contexts**: Added technical environment details for Homelab infra, K3s cluster, Network mesh, Java Spring ecosystem, and Proxmox VE.
- **Workflows**: Added SOPs for architecture design, code review, playbook generation, system migration, and troubleshooting.
- **Profiles**: Added 5 ready-to-use playbooks (`ansible-engineer`, `java-architect`, `k3s-admin`, `pve-infra-migration`, `security-audit`).
