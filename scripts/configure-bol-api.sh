#!/usr/bin/env bash
set -euo pipefail

RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-airco-tracker-nl-rg}"
GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-ProgrammerAsahi/airco-tracking-nl}"

command -v az >/dev/null || { echo "Azure CLI (az) is required." >&2; exit 1; }
command -v gh >/dev/null || { echo "GitHub CLI (gh) is required." >&2; exit 1; }
az account show >/dev/null || { echo "Run 'az login' first." >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "Run 'gh auth login' first." >&2; exit 1; }

VAULT_NAME="$(az deployment group show \
  --name airco-foundation \
  --resource-group "$RESOURCE_GROUP" \
  --query properties.outputs.keyVaultUrl.value \
  --output tsv | sed -E 's#https://([^.]+).*#\1#')"
VAULT_ID="$(az keyvault show --name "$VAULT_NAME" --query id --output tsv)"
USER_OBJECT_ID="$(az ad signed-in-user show --query id --output tsv)"

ROLE_ASSIGNMENT_ID="$(az role assignment list \
  --assignee "$USER_OBJECT_ID" \
  --scope "$VAULT_ID" \
  --role "Key Vault Secrets Officer" \
  --query '[0].id' \
  --output tsv)"
CREATED_ROLE_ASSIGNMENT=false
if [[ -z "$ROLE_ASSIGNMENT_ID" ]]; then
  ROLE_ASSIGNMENT_ID="$(az role assignment create \
    --assignee-object-id "$USER_OBJECT_ID" \
    --assignee-principal-type User \
    --scope "$VAULT_ID" \
    --role "Key Vault Secrets Officer" \
    --query id \
    --output tsv)"
  CREATED_ROLE_ASSIGNMENT=true
fi

cleanup() {
  unset BOL_CLIENT_ID BOL_CLIENT_SECRET
  if [[ "$CREATED_ROLE_ASSIGNMENT" == "true" ]]; then
    az role assignment delete --ids "$ROLE_ASSIGNMENT_ID" --only-show-errors || true
  fi
}
trap cleanup EXIT

read -r -p "bol Marketing API Client ID: " BOL_CLIENT_ID
read -r -s -p "bol Marketing API Client Secret: " BOL_CLIENT_SECRET
echo

if [[ -z "$BOL_CLIENT_ID" || -z "$BOL_CLIENT_SECRET" ]]; then
  echo "Client ID and Client Secret are required." >&2
  exit 1
fi

set_secret() {
  local name="$1"
  local value="$2"
  local attempt
  for attempt in {1..12}; do
    if az keyvault secret set --vault-name "$VAULT_NAME" --name "$name" --value "$value" --output none 2>/dev/null; then
      return 0
    fi
    sleep 10
  done
  echo "Could not write $name after waiting for Azure RBAC propagation." >&2
  return 1
}

set_secret bol-client-id "$BOL_CLIENT_ID"
set_secret bol-client-secret "$BOL_CLIENT_SECRET"
unset BOL_CLIENT_ID BOL_CLIENT_SECRET

gh variable set BOL_BACKEND --repo "$GITHUB_REPOSITORY" --body "marketing_api"
gh variable set KEY_VAULT_SECRET_MAP \
  --repo "$GITHUB_REPOSITORY" \
  --body "BOL_CLIENT_ID=bol-client-id,BOL_CLIENT_SECRET=bol-client-secret"

gh workflow run deploy.yml --repo "$GITHUB_REPOSITORY" --ref main
echo "bol Marketing Catalog API enabled. GitHub deployment started."
