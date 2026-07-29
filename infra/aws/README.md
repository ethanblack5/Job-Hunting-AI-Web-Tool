# AWS deployment hardening

This workflow addresses Issue #57 by:

1. Restricting all public ingress rules on the EC2 security group.
2. Allowing only explicitly supplied IPv4 CIDRs on the required TCP ports.
3. Tagging the Chroma EBS volume.
4. Creating or updating an Amazon Data Lifecycle Manager policy that takes
   scheduled EBS snapshots and removes snapshots beyond the retention count.

The script is plan-only by default. It does not change AWS until `--apply` is
provided.

## Prerequisites

- AWS CLI v2 installed and authenticated.
- Permission to inspect and modify EC2 security groups and volume tags.
- Permission to create the DLM default role and lifecycle policies.
- The EC2 security group ID and the EBS volume ID containing the Chroma index.
- Stable public IPv4 addresses for each developer or network that needs access.

Do not use temporary residential IP addresses without planning how access will
be updated when they change. Prefer a VPN, office NAT gateway, or other stable
egress address.

## Configure

```bash
export AWS_REGION="us-east-2"
export SECURITY_GROUP_ID="sg-0123456789abcdef0"
export EBS_VOLUME_ID="vol-0123456789abcdef0"
export ALLOWED_CIDRS="203.0.113.10/32,198.51.100.24/32"
```

The default allowed ports are SSH (`22`) and Chroma (`8000`). Override the list
if this EC2 instance exposes other services:

```bash
export ALLOWED_PORTS="22,8000"
```

Snapshot defaults are one snapshot every 24 hours at 03:00 UTC, retaining the
latest seven snapshots. They can be overridden:

```bash
export SNAPSHOT_INTERVAL_HOURS="24"
export SNAPSHOT_TIME_UTC="03:00"
export SNAPSHOT_RETENTION_COUNT="7"
```

Supported snapshot intervals are `1`, `2`, `3`, `4`, `6`, `8`, `12`, and `24`
hours.

## Review the plan

```bash
./infra/aws/harden_deployment.sh
```

Confirm the AWS account, Region, security group, volume, CIDRs, ports, snapshot
frequency, and retention count shown in the output.

## Apply

Keep an existing SSH session open while applying security-group changes so you
can verify a new session before disconnecting.

```bash
./infra/aws/harden_deployment.sh --apply
```

The script adds the known-IP rules before removing public rules. It removes
every inbound rule sourced from `0.0.0.0/0` or `::/0`; rules sourced from other
security groups or private CIDRs are preserved.

## Verify

Confirm there are no public ingress rules:

```bash
aws ec2 describe-security-group-rules \
  --region "$AWS_REGION" \
  --filters "Name=group-id,Values=$SECURITY_GROUP_ID" \
  --query "SecurityGroupRules[?IsEgress==\`false\`]"
```

Confirm the policy is enabled:

```bash
aws dlm get-lifecycle-policies \
  --region "$AWS_REGION" \
  --query "Policies[?Description=='Chroma index EBS snapshots']"
```

After the first scheduled run, confirm that a snapshot exists:

```bash
aws ec2 describe-snapshots \
  --region "$AWS_REGION" \
  --owner-ids self \
  --filters "Name=volume-id,Values=$EBS_VOLUME_ID"
```

Periodically test restoration to a new EBS volume. A snapshot that has never
been restored is not a verified backup.

## Rollback

Add a replacement known-IP rule before removing an old one:

```bash
aws ec2 authorize-security-group-ingress \
  --region "$AWS_REGION" \
  --group-id "$SECURITY_GROUP_ID" \
  --protocol tcp \
  --port 22 \
  --cidr "NEW_IP/32"
```

Disable, rather than immediately delete, the lifecycle policy while
investigating backup problems:

```bash
aws dlm update-lifecycle-policy \
  --region "$AWS_REGION" \
  --policy-id "policy-REPLACE_ME" \
  --state DISABLED
```

Amazon Data Lifecycle Manager uses target tags to select volumes. Removing the
target tag stops new scheduled snapshots for that volume, but existing
snapshots may require separate lifecycle or manual cleanup.
