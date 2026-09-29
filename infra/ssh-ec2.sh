#!/usr/bin/env bash
# infra/ssh-ec2.sh — SSH to the DevSecOps box, keeping the security group in sync.
#
# Why this exists: this workstation is multi-homed and its egress IP flips
# between WAN paths (observed: 103.211.36.242 and 124.123.14.2). A hand-pinned
# /32 in the security group goes stale without warning and SSH starts timing
# out with no useful error. So: discover the current egress IP(s), make sure
# each is allowed, drop the ones that no longer are, then connect.
#
# Usage:  ./infra/ssh-ec2.sh 'docker ps'
#         ./infra/ssh-ec2.sh              # interactive shell
#
# Durable alternative: SSM Session Manager. No inbound port at all, immune to
# this whole problem. See README for the three CLI calls that enable it.
set -euo pipefail

REGION=${EC2_REGION:-ap-south-2}
SG=${EC2_SG:-sg-0fe662149c0d4079a}
INSTANCE_IP=${EC2_HOST:-16.113.100.208}
KEY=${EC2_KEY:-$(cd "$(dirname "$0")" && pwd)/../devsecops.pem}
SSH_USER=${EC2_USER:-ubuntu}
# Ports kept in sync with this workstation's egress IPs. 22 for shell access,
# 5000 so the running container is reachable from a browser.
PORTS=${EC2_PORTS:-22 5000}

# Ask several echo services; this box answers with different IPs depending on
# which uplink the request happens to leave by.
discover_ips() {
  local u ip
  for u in https://api.ipify.org https://ifconfig.me https://ipinfo.io/ip https://checkip.amazonaws.com; do
    ip=$(curl -fsS --max-time 6 "$u" 2>/dev/null | tr -d '[:space:]' || true)
    [[ $ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] && echo "$ip"
  done | sort -u
}

CURRENT=$(discover_ips)
[[ -n $CURRENT ]] || { echo "could not determine egress IP" >&2; exit 1; }

for port in $PORTS; do
  ALLOWED=$(aws ec2 describe-security-groups --region "$REGION" --group-ids "$SG" \
    --query "SecurityGroups[0].IpPermissions[?FromPort==\`$port\`].IpRanges[].CidrIp" \
    --output text | tr '\t' '\n' | sed 's|/32$||')

  for ip in $CURRENT; do
    if ! grep -qx "$ip" <<<"$ALLOWED"; then
      echo "+ $port <- $ip"
      aws ec2 authorize-security-group-ingress --region "$REGION" --group-id "$SG" \
        --protocol tcp --port "$port" --cidr "$ip/32" >/dev/null
    fi
  done

  # No pruning on purpose. This workstation has two uplinks and the echo
  # services do not reliably report both, so "not seen this second" does not
  # mean "not needed" — pruning here revokes a rule that is needed moments
  # later. Rules are cheap; a locked-out shell is not. Prune by hand if the
  # group ever grows. (The durable fix is SSM and no inbound 22 at all.)
done

exec ssh -i "$KEY" \
  -o StrictHostKeyChecking=accept-new \
  -o ConnectTimeout=20 \
  "$SSH_USER@$INSTANCE_IP" "$@"
