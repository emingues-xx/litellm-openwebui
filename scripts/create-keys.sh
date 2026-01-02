#!/bin/bash

LITELLM_URL="http://localhost:4000"
MASTER_KEY="sk-1234-change-this-master-key"

echo "==================================================================="
echo "Criando Virtual Keys para controle de acesso por grupo"
echo "==================================================================="
echo ""

# 1. Chave para grupo VENDAS
# Acesso a: gpt-4, claude-sonnet (modelos premium)
echo "1. Criando chave para grupo VENDAS..."
VENDAS_RESPONSE=$(curl -s -X POST "${LITELLM_URL}/key/generate" \
  -H "Authorization: Bearer ${MASTER_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "models": ["gpt-4", "claude-sonnet"],
    "duration": null,
    "key_alias": "vendas-team",
    "team_id": "vendas",
    "metadata": {
      "group": "vendas",
      "description": "Sales team - access to premium models"
    }
  }')

VENDAS_KEY=$(echo $VENDAS_RESPONSE | jq -r '.key')
echo "   ✅ Chave criada: ${VENDAS_KEY:0:20}..."
echo ""

# 2. Chave para grupo GERAL
# Acesso a: gpt-3.5-turbo (modelo básico)
echo "2. Criando chave para grupo GERAL..."
GERAL_RESPONSE=$(curl -s -X POST "${LITELLM_URL}/key/generate" \
  -H "Authorization: Bearer ${MASTER_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "models": ["gpt-3.5-turbo"],
    "duration": null,
    "key_alias": "geral-team",
    "team_id": "geral",
    "metadata": {
      "group": "geral",
      "description": "General team - access to basic models"
    }
  }')

GERAL_KEY=$(echo $GERAL_RESPONSE | jq -r '.key')
echo "   ✅ Chave criada: ${GERAL_KEY:0:20}..."
echo ""

echo "==================================================================="
echo "✅ Virtual Keys criadas com sucesso!"
echo "==================================================================="
echo ""
echo "Adicione estas chaves no arquivo .env:"
echo ""
echo "VENDAS_KEY=${VENDAS_KEY}"
echo "GERAL_KEY=${GERAL_KEY}"
echo ""
