# Beeper Server container

An isolated container for the official stable Linux Beeper Server. The image
contains a small launcher; the proprietary runtime is downloaded directly from
Beeper on first start and checked against its published SHA-512 checksum.

The current package pins version 4.3.308. It never signs in automatically, imports
a desktop profile, resets a recovery key, or exposes a public API port.

## Deployment

1. Build this Dockerfile on a Linux container host.
2. Attach one persistent volume at `/data`; use a single replica.
3. Keep all networking private. The API listens on localhost, port 23374.
4. Start the container and run `python /app/probe.py --isolated-test` in its terminal.
5. Verify that the volume survives container replacement before signing in.

The provider account's free-plan eligibility, allowed compute size, disk allowance,
and aggregate resource use must be checked in its dashboard before deployment.
Do not enable a paid plan or enter a payment method as part of this setup.

Northflank was investigated as an alternative. Its pricing page advertises a free Sandbox
with always-on workloads and up to $20/month of resources. Its billing guide also
says payment details are required, so the actual account workflow must resolve
that discrepancy. Persistent disk eligibility on the free account is not yet
verified. This repository has not provisioned any provider account or server.

## Sign in after the host is verified

Use the official Beeper CLI's email-code flow from a trusted provider terminal or
an authenticated private connection. Approve the new device from an existing
Beeper device. Never reset the existing recovery key. Login codes, recovery
keys, profile databases, and access tokens stay outside this repository.

The included CI uses a blank profile to verify a resource-limited Linux container,
authentication enforcement, and profile persistence across container replacement.
It does not establish real account sync, Telegram access, or Mac-off operation.

## Verification status

The latest executed check, [run 43869401539](https://github.com/5Ni4/beeper-free-host/actions/runs/43869401539),
confirmed initial startup, startup after container replacement, persisted profile
files, unauthenticated API/MCP rejection, and no public port. It then failed in
the runtime-user assertion because the test searched by a process name which
the server does not use. The assertion now checks the init process's child UID;
that revised assertion has not been executed. The complete CI check remains
unverified, and this package has not been deployed to a hosting provider.

CI is manual-only to avoid generating repeated failure-notification emails during
the parallel hosting work. There are no scheduled or push-triggered runs.

## Sources

- https://github.com/beeper/cli/blob/main/packages/cli/docs/setup.md
- https://northflank.com/pricing
- https://northflank.com/docs/v1/application/billing/pricing-on-northflank
- https://northflank.com/docs/v1/application/billing/resource-plans-and-quotas
- https://docs.run.claw.cloud/clawcloud-run/pricing
- https://docs.run.claw.cloud/clawcloud-run/guide/app-launchpad/persistent-storage
