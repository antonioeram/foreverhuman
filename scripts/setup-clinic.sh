#!/bin/bash
# =============================================================================
# foreverhuman.health — Setup clinică nouă pe VPS
# Rulează pe un VPS Ubuntu 22.04+ cu Docker și Docker Compose instalate.
#
# Usage:
#   curl -fsSL https://setup.foreverhuman.health/setup.sh | bash
#   sau
#   ./scripts/setup-clinic.sh
# =============================================================================

set -euo pipefail

REPO_URL="https://github.com/foreverhuman/platform"
INSTALL_DIR="/opt/foreverhuman"
COMPOSE_FILE="$INSTALL_DIR/infra/docker-compose.clinic.yml"

echo "=================================="
echo " foreverhuman.health — Clinic Setup"
echo "=================================="

# ---------------------------------------------------------------------------
# Verificări preliminare
# ---------------------------------------------------------------------------
check_requirements() {
    echo "→ Verificare cerințe sistem..."

    if ! command -v docker &>/dev/null; then
        echo "❌ Docker nu e instalat. Instalează: https://docs.docker.com/engine/install/"
        exit 1
    fi

    if ! command -v docker compose &>/dev/null; then
        echo "❌ Docker Compose v2 nu e instalat."
        exit 1
    fi

    DOCKER_VERSION=$(docker --version | awk '{print $3}' | tr -d ',')
    echo "✅ Docker $DOCKER_VERSION"

    # Verificare RAM minim (4GB recomandat)
    RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
    if [ "$RAM_MB" -lt 3500 ]; then
        echo "⚠️  RAM disponibil: ${RAM_MB}MB. Recomandat minim 4GB."
    else
        echo "✅ RAM: ${RAM_MB}MB"
    fi

    # Verificare disk (minim 20GB)
    DISK_GB=$(df -BG / | awk 'NR==2{print $4}' | tr -d 'G')
    if [ "$DISK_GB" -lt 20 ]; then
        echo "⚠️  Spațiu disk disponibil: ${DISK_GB}GB. Recomandat minim 20GB."
    else
        echo "✅ Disk: ${DISK_GB}GB disponibil"
    fi
}

# ---------------------------------------------------------------------------
# Colectare parametri clinică
# ---------------------------------------------------------------------------
collect_parameters() {
    echo ""
    echo "→ Configurare clinică..."

    read -rp "Domeniu clinică (ex: clinic.example.com): " DOMAIN
    read -rp "Nume clinică (ex: Clinica Dr. Ionescu): " CLINIC_NAME
    read -rp "Email admin: " ADMIN_EMAIL

    # Generare credențiale automat
    CLINIC_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
    POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    SECRET_KEY=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-64)
    N8N_KEY=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-32)

    echo ""
    echo "✅ CLINIC_ID generat: $CLINIC_ID"
    echo "✅ Credențiale generate automat."
    echo ""
    read -rp "LLM Provider (anthropic/ollama) [anthropic]: " LLM_PROVIDER
    LLM_PROVIDER=${LLM_PROVIDER:-anthropic}

    if [ "$LLM_PROVIDER" = "anthropic" ]; then
        read -rp "Anthropic API Key (sk-ant-...): " ANTHROPIC_API_KEY
        OPENAI_API_KEY=""
        read -rp "OpenAI API Key pentru embeddings (sk-...) [Enter pentru Ollama]: " OPENAI_API_KEY
        EMBEDDING_PROVIDER="openai"
        [ -z "$OPENAI_API_KEY" ] && EMBEDDING_PROVIDER="ollama"
    else
        ANTHROPIC_API_KEY=""
        OPENAI_API_KEY=""
        EMBEDDING_PROVIDER="ollama"
        echo "ℹ️  Folosind Ollama local — asigură-te că modelele sunt descărcate."
    fi
}

# ---------------------------------------------------------------------------
# Instalare
# ---------------------------------------------------------------------------
install() {
    echo ""
    echo "→ Creare directoare..."
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"

    echo "→ Clonare repository..."
    if [ -d ".git" ]; then
        git pull origin main
    else
        git clone "$REPO_URL" .
    fi

    echo "→ Creare fișier .env..."
    cat > "$INSTALL_DIR/infra/.env" <<EOF
CLINIC_ID=$CLINIC_ID
DOMAIN=$DOMAIN
ENVIRONMENT=production
LOG_LEVEL=info
POSTGRES_USER=foreverhuman
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_DB=foreverhuman_clinic
SECRET_KEY=$SECRET_KEY
N8N_ENCRYPTION_KEY=$N8N_KEY
LLM_PROVIDER=$LLM_PROVIDER
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
OPENAI_API_KEY=$OPENAI_API_KEY
EMBEDDING_PROVIDER=$EMBEDDING_PROVIDER
ADMIN_EMAIL=$ADMIN_EMAIL
API_VERSION=latest
INFRA_AGENT_VERSION=latest
EOF

    chmod 600 "$INSTALL_DIR/infra/.env"
    echo "✅ .env creat și securizat (chmod 600)"

    echo "→ Pull imagini Docker..."
    docker compose -f "$COMPOSE_FILE" --env-file "$INSTALL_DIR/infra/.env" pull

    echo "→ Pornire servicii..."
    docker compose -f "$COMPOSE_FILE" --env-file "$INSTALL_DIR/infra/.env" up -d

    echo "→ Așteptare servicii healthy..."
    sleep 10

    # Verificare API
    MAX_RETRIES=12
    COUNT=0
    until curl -sf "http://localhost:8000/health" &>/dev/null; do
        COUNT=$((COUNT + 1))
        if [ "$COUNT" -ge "$MAX_RETRIES" ]; then
            echo "❌ API-ul nu răspunde după $(($MAX_RETRIES * 5))s. Verifică: docker compose logs api"
            exit 1
        fi
        echo "⏳ Așteptare API... ($COUNT/$MAX_RETRIES)"
        sleep 5
    done

    echo ""
    echo "========================================="
    echo " ✅ foreverhuman.health — Setup complet!"
    echo "========================================="
    echo ""
    echo "  Clinic ID:  $CLINIC_ID"
    echo "  Domeniu:    https://$DOMAIN"
    echo "  API Health: https://$DOMAIN/health"
    echo "  n8n:        https://$DOMAIN/n8n/"
    echo ""
    echo "  ⚠️  Salvează aceste credențiale în loc sigur:"
    echo "  DB Password: $POSTGRES_PASSWORD"
    echo ""
    echo "  📄 Logs: docker compose -f $COMPOSE_FILE logs -f"
    echo ""
    echo "  Pasul următor: configurează DNS $DOMAIN → $(curl -s ifconfig.me)"
    echo "  SSL (Let's Encrypt) se va activa automat după DNS propagation."
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
check_requirements
collect_parameters
install
