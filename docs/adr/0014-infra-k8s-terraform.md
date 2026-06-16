# ADR-0014: Docker + Kubernetes + Terraform + GitHub Actions
**Status:** Accepted
## Context
We need reproducible builds, scalable deploys (seasonal peaks), multi-region, and IaC.
## Decision
**Docker** images; **Kubernetes** (Helm) for runtime; **Terraform** for cloud infra; **GitHub Actions**
for CI/CD. Multi-region for residency + DR.
## Consequences
+ Portable, autoscaling, reproducible; standard tooling.
− K8s operational overhead; use managed control plane.
