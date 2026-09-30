#!/usr/bin/env bash
# infra/ssh-ec2.sh — Optional helper for remote EC2 test environments only.
#
# NOTE: EC2 is NOT mandatory for this project.
# The DevSecOps pipeline and deployments run locally or on any server with Docker.
# This script is provided only as a convenience helper if you choose to connect
# to an optional remote AWS EC2 sandbox without breaking firewall rules.
#
# Why this exists: a workstation can be multi-homed, with its egress IP flipping
# between WAN paths. A hand-pinned /32 in the security group then goes stale
# without warning and SSH starts timing out with no useful error. So: discover
# the current egress IP(s) and make sure each is allowed before connecting.
#
# It deliberately does NOT prune. Pruning on a flapping connection revokes the
# rule that is needed a second later, which is how you lock yourself out. The
# durable alternative is SSM Session Manager, which needs no inbound port at all.
#
# Usage:  ./infra/ssh-ec2.sh 'docker ps'
#         ./infra/ssh-ec2.sh              # interactive shell
set -euo pipefail

# ------------------------------------------------------------------ settings
# No defaults for the target, the security group or the key. This is a public
# repository, so it must not ship one person's instance address, group id or key
# path. Failing loudly is better than silently connecting to the wrong host.
REGION=${EC2_REGION:-ap-south-2}
SG=${EC2_SG:?set EC2_SG to the security group id}
INSTANCE_IP=${EC2_HOST:?set EC2_HOST to the instance address}
KEY=${EC2_KEY:?set EC2_KEY to the path of the private key}
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
