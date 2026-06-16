# ADR-0010: OIDC + RBAC, mTLS service-to-service
**Status:** Accepted
## Context
Professional users, SSO/SCIM for firms, and secure service mesh are required.
## Decision
**OIDC** for user auth (SSO/SCIM for enterprise), **RBAC** for authorization, **mTLS** between
internal services. Secrets in a managed vault.
## Consequences
+ Standard, enterprise-ready; least privilege.
− Identity infra to operate; use a managed IdP where possible.
