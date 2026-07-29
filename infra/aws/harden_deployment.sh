#!/usr/bin/env bash
#
# Restrict an EC2 security group to known IPv4 CIDRs and configure an
# Amazon Data Lifecycle Manager policy for the Chroma EBS volume.
#
# The script is plan-only unless --apply is supplied.

set -euo pipefail

APPLY=false
if [[ "${1:-}" == "--apply" ]]; then
    APPLY=true
elif [[ -n "${1:-}" ]]; then
    echo "Usage: $0 [--apply]" >&2
    exit 2
fi

required_variables=(
    AWS_REGION
    SECURITY_GROUP_ID
    EBS_VOLUME_ID
    ALLOWED_CIDRS
)

for variable in "${required_variables[@]}"; do
    if [[ -z "${!variable:-}" ]]; then
        echo "Missing required environment variable: ${variable}" >&2
        exit 2
    fi
done

command -v aws >/dev/null 2>&1 || {
    echo "AWS CLI v2 is required." >&2
    exit 2
}

IFS=',' read -r -a allowed_cidrs <<< "${ALLOWED_CIDRS}"
IFS=',' read -r -a allowed_ports <<< "${ALLOWED_PORTS:-22,8000}"

for cidr in "${allowed_cidrs[@]}"; do
    if [[ ! "${cidr}" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/[0-9]+$ ]]; then
        echo "ALLOWED_CIDRS must contain IPv4 CIDRs, not '${cidr}'." >&2
        exit 2
    fi
    if [[ "${cidr}" == "0.0.0.0/0" ]]; then
        echo "Refusing to allow public IPv4 access." >&2
        exit 2
    fi
done

for port in "${allowed_ports[@]}"; do
    if [[ ! "${port}" =~ ^[0-9]+$ ]] || (( port < 1 || port > 65535 )); then
        echo "Invalid port in ALLOWED_PORTS: '${port}'." >&2
        exit 2
    fi
done

snapshot_interval="${SNAPSHOT_INTERVAL_HOURS:-24}"
snapshot_retention="${SNAPSHOT_RETENTION_COUNT:-7}"
snapshot_time="${SNAPSHOT_TIME_UTC:-03:00}"
policy_description="${DLM_POLICY_DESCRIPTION:-Chroma index EBS snapshots}"
target_tag_key="${DLM_TARGET_TAG_KEY:-ChromaSnapshotSchedule}"
target_tag_value="${DLM_TARGET_TAG_VALUE:-daily}"

if [[ ! "${snapshot_interval}" =~ ^(1|2|3|4|6|8|12|24)$ ]]; then
    echo "SNAPSHOT_INTERVAL_HOURS must be 1, 2, 3, 4, 6, 8, 12, or 24." >&2
    exit 2
fi
if [[ ! "${snapshot_retention}" =~ ^[1-9][0-9]*$ ]]; then
    echo "SNAPSHOT_RETENTION_COUNT must be greater than zero." >&2
    exit 2
fi
if [[ ! "${snapshot_time}" =~ ^([01][0-9]|2[0-3]):[0-5][0-9]$ ]]; then
    echo "SNAPSHOT_TIME_UTC must use HH:MM UTC format." >&2
    exit 2
fi

aws_args=(--region "${AWS_REGION}" --no-cli-pager)

echo "Checking AWS identity and target resources..."
aws sts get-caller-identity "${aws_args[@]}" --output table
aws ec2 describe-security-groups \
    "${aws_args[@]}" \
    --group-ids "${SECURITY_GROUP_ID}" \
    --output table >/dev/null
aws ec2 describe-volumes \
    "${aws_args[@]}" \
    --volume-ids "${EBS_VOLUME_ID}" \
    --output table >/dev/null

echo
echo "Plan:"
echo "  Security group: ${SECURITY_GROUP_ID}"
echo "  Allowed IPv4 CIDRs: ${ALLOWED_CIDRS}"
echo "  Allowed TCP ports: ${ALLOWED_PORTS:-22,8000}"
echo "  Remove every remaining 0.0.0.0/0 and ::/0 ingress rule"
echo "  EBS volume: ${EBS_VOLUME_ID}"
echo "  Snapshot every ${snapshot_interval} hours at ${snapshot_time} UTC"
echo "  Retain ${snapshot_retention} snapshots"

if [[ "${APPLY}" != "true" ]]; then
    echo
    echo "Plan only. Re-run with --apply to make these changes."
    exit 0
fi

echo
echo "Authorizing known CIDRs before removing public rules..."
for cidr in "${allowed_cidrs[@]}"; do
    for port in "${allowed_ports[@]}"; do
        set +e
        output="$(
            aws ec2 authorize-security-group-ingress \
                "${aws_args[@]}" \
                --group-id "${SECURITY_GROUP_ID}" \
                --protocol tcp \
                --port "${port}" \
                --cidr "${cidr}" \
                --tag-specifications \
                "ResourceType=security-group-rule,Tags=[{Key=ManagedBy,Value=JobHunterHardening}]" \
                2>&1
        )"
        status=$?
        set -e
        if (( status != 0 )) && [[ "${output}" != *"InvalidPermission.Duplicate"* ]]; then
            echo "${output}" >&2
            exit "${status}"
        fi
    done
done

public_rule_ids="$(
    aws ec2 describe-security-group-rules \
        "${aws_args[@]}" \
        --filters "Name=group-id,Values=${SECURITY_GROUP_ID}" \
        --query \
        "SecurityGroupRules[?IsEgress==\`false\` && (CidrIpv4==\`0.0.0.0/0\` || CidrIpv6==\`::/0\`)].SecurityGroupRuleId" \
        --output text
)"

if [[ -n "${public_rule_ids}" && "${public_rule_ids}" != "None" ]]; then
    read -r -a public_rules <<< "${public_rule_ids}"
    aws ec2 revoke-security-group-ingress \
        "${aws_args[@]}" \
        --group-id "${SECURITY_GROUP_ID}" \
        --security-group-rule-ids "${public_rules[@]}"
fi

remaining_public_rules="$(
    aws ec2 describe-security-group-rules \
        "${aws_args[@]}" \
        --filters "Name=group-id,Values=${SECURITY_GROUP_ID}" \
        --query \
        "SecurityGroupRules[?IsEgress==\`false\` && (CidrIpv4==\`0.0.0.0/0\` || CidrIpv6==\`::/0\`)].SecurityGroupRuleId" \
        --output text
)"
if [[ -n "${remaining_public_rules}" && "${remaining_public_rules}" != "None" ]]; then
    echo "Public ingress rules remain: ${remaining_public_rules}" >&2
    exit 1
fi

echo "Tagging the EBS volume for the snapshot policy..."
aws ec2 create-tags \
    "${aws_args[@]}" \
    --resources "${EBS_VOLUME_ID}" \
    --tags \
    "Key=${target_tag_key},Value=${target_tag_value}" \
    "Key=ManagedBy,Value=JobHunterHardening"

echo "Ensuring the default Data Lifecycle Manager role exists..."
set +e
role_output="$(
    aws dlm create-default-role \
        "${aws_args[@]}" \
        --resource-type snapshot \
        2>&1
)"
role_status=$?
set -e
if (( role_status != 0 )) && [[ "${role_output}" != *"already exists"* ]]; then
    echo "${role_output}" >&2
    exit "${role_status}"
fi

execution_role_arn="$(
    aws iam get-role \
        --role-name AWSDataLifecycleManagerDefaultRole \
        --query "Role.Arn" \
        --output text \
        --no-cli-pager
)"

policy_file="$(mktemp)"
trap 'rm -f "${policy_file}"' EXIT
cat > "${policy_file}" <<EOF
{
  "PolicyType": "EBS_SNAPSHOT_MANAGEMENT",
  "ResourceTypes": ["VOLUME"],
  "TargetTags": [
    {"Key": "${target_tag_key}", "Value": "${target_tag_value}"}
  ],
  "Schedules": [
    {
      "Name": "ChromaIndexSnapshots",
      "CopyTags": true,
      "CreateRule": {
        "Interval": ${snapshot_interval},
        "IntervalUnit": "HOURS",
        "Times": ["${snapshot_time}"]
      },
      "RetainRule": {"Count": ${snapshot_retention}},
      "TagsToAdd": [
        {"Key": "Application", "Value": "JobHunter"},
        {"Key": "Data", "Value": "ChromaIndex"}
      ]
    }
  ]
}
EOF

policy_id="$(
    aws dlm get-lifecycle-policies \
        "${aws_args[@]}" \
        --query "Policies[?Description==\`${policy_description}\`].PolicyId | [0]" \
        --output text
)"

if [[ -n "${policy_id}" && "${policy_id}" != "None" ]]; then
    echo "Updating existing snapshot policy ${policy_id}..."
    aws dlm update-lifecycle-policy \
        "${aws_args[@]}" \
        --policy-id "${policy_id}" \
        --execution-role-arn "${execution_role_arn}" \
        --state ENABLED \
        --description "${policy_description}" \
        --policy-details "file://${policy_file}"
else
    echo "Creating snapshot policy..."
    policy_id="$(
        aws dlm create-lifecycle-policy \
            "${aws_args[@]}" \
            --execution-role-arn "${execution_role_arn}" \
            --description "${policy_description}" \
            --state ENABLED \
            --policy-details "file://${policy_file}" \
            --query "PolicyId" \
            --output text
    )"
fi

echo
echo "Deployment hardened successfully."
echo "  DLM policy: ${policy_id}"
echo "  Security group: ${SECURITY_GROUP_ID}"
echo "  EBS volume: ${EBS_VOLUME_ID}"
