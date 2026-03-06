#!/bin/bash
# =============================================================================
# foreverhuman.health — Creare VM-uri pe Proxmox
# Rulează direct pe host-ul Proxmox ca root
# =============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# Configurare
# ---------------------------------------------------------------------------
CLOUD_IMAGE="/var/lib/vz/template/iso/ubuntu-24.04-cloud.img"
STORAGE="local-lvm"
BRIDGE="vmbr0"
GW="10.0.10.1"
DNS="8.8.8.8"

# VM Clinic
CLINIC_VMID=105
CLINIC_NAME="foreverhuman-clinic"
CLINIC_IP="10.0.10.105"
CLINIC_RAM=8192    # 8GB
CLINIC_CORES=4
CLINIC_DISK=100    # GB

# VM KB
KB_VMID=106
KB_NAME="foreverhuman-kb"
KB_IP="10.0.10.106"
KB_RAM=4096        # 4GB
KB_CORES=2
KB_DISK=80         # GB

# Credențiale VM-uri
VM_USER="ubuntu"
VM_PASS="ForeverHuman2026!"

# ---------------------------------------------------------------------------
# SSH Key
# ---------------------------------------------------------------------------
echo "→ Generare SSH key pentru foreverhuman..."
if [ ! -f /root/.ssh/foreverhuman_key ]; then
    ssh-keygen -t ed25519 -f /root/.ssh/foreverhuman_key -N "" -C "foreverhuman-deploy"
fi
SSH_PUB=$(cat /root/.ssh/foreverhuman_key.pub)
echo "✅ SSH key: /root/.ssh/foreverhuman_key"

# ---------------------------------------------------------------------------
# Funcție creare VM
# ---------------------------------------------------------------------------
create_vm() {
    local VMID=$1
    local NAME=$2
    local IP=$3
    local RAM=$4
    local CORES=$5
    local DISK=$6

    echo ""
    echo "→ Creare VM $VMID ($NAME) — IP: $IP, RAM: ${RAM}MB, Cores: $CORES, Disk: ${DISK}GB"

    # Verificare dacă VM există deja
    if qm status $VMID &>/dev/null; then
        echo "⚠️  VM $VMID există deja. Skip."
        return
    fi

    # Creare VM de bază
    qm create $VMID \
        --name "$NAME" \
        --memory $RAM \
        --cores $CORES \
        --sockets 1 \
        --cpu host \
        --net0 virtio,bridge=$BRIDGE \
        --ostype l26 \
        --agent enabled=1 \
        --onboot 1 \
        --boot order=scsi0

    # Import disk din cloud image
    echo "  → Import disk..."
    qm importdisk $VMID "$CLOUD_IMAGE" $STORAGE --format qcow2

    # Configurare disk ca SCSI
    qm set $VMID --scsi0 "${STORAGE}:vm-${VMID}-disk-0,discard=on,ssd=1"

    # Resize disk
    qm resize $VMID scsi0 "${DISK}G"

    # Cloud-init drive
    qm set $VMID --ide2 "${STORAGE}:cloudinit"

    # Boot din disk
    qm set $VMID --boot order=scsi0

    # Serial console (necesar pentru cloud images)
    qm set $VMID --serial0 socket --vga serial0

    # Cloud-init configurare
    qm set $VMID \
        --ciuser "$VM_USER" \
        --cipassword "$VM_PASS" \
        --sshkeys <(echo "$SSH_PUB") \
        --ipconfig0 "ip=${IP}/24,gw=${GW}" \
        --nameserver "$DNS" \
        --searchdomain "foreverhuman.local"

    echo "✅ VM $VMID ($NAME) creat."
}

# ---------------------------------------------------------------------------
# Creare VM-uri
# ---------------------------------------------------------------------------
create_vm $CLINIC_VMID "$CLINIC_NAME" "$CLINIC_IP" $CLINIC_RAM $CLINIC_CORES $CLINIC_DISK
create_vm $KB_VMID "$KB_NAME" "$KB_IP" $KB_RAM $KB_CORES $KB_DISK

# ---------------------------------------------------------------------------
# Pornire VM-uri
# ---------------------------------------------------------------------------
echo ""
echo "→ Pornire VM-uri..."
qm start $CLINIC_VMID
qm start $KB_VMID

echo ""
echo "→ Așteptare boot (45s)..."
sleep 45

# ---------------------------------------------------------------------------
# Verificare
# ---------------------------------------------------------------------------
echo ""
echo "=== STATUS VM-URI ==="
qm list | grep -E "foreverhuman|VMID"

echo ""
echo "=== PING TEST ==="
ping -c 2 $CLINIC_IP && echo "✅ Clinic VM accesibil" || echo "❌ Clinic VM nu răspunde încă"
ping -c 2 $KB_IP     && echo "✅ KB VM accesibil"     || echo "❌ KB VM nu răspunde încă"

echo ""
echo "========================================="
echo " ✅ VM-uri create!"
echo "========================================="
echo ""
echo "  foreverhuman-clinic: ssh ubuntu@$CLINIC_IP"
echo "  foreverhuman-kb:     ssh ubuntu@$KB_IP"
echo "  SSH Key:             /root/.ssh/foreverhuman_key"
echo "  Password:            $VM_PASS"
echo ""
echo "  De pe Proxmox:"
echo "  ssh -i /root/.ssh/foreverhuman_key ubuntu@$CLINIC_IP"
echo "  ssh -i /root/.ssh/foreverhuman_key ubuntu@$KB_IP"
