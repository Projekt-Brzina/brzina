# This script will clean up any previous standalone Helm releases and set up the full brzina stack from scratch.
# Usage: Run in PowerShell from the project root (brzina)

# Set namespace variable
$namespace = "brzina"

# 1. Delete all previous standalone releases (ignore errors if not present)
$releases = @(
    "api", "auth", "booking", "car", "payment", "frontend", "grafana", "prometheus", "kafka", "postgres", "nginx-ingress", "ingress", "template"
)
foreach ($release in $releases) {
    helm uninstall $release -n $namespace 2>$null
}

# 2. Delete the namespace (removes all resources, including lingering ServiceAccounts, PVCs, etc.)
kubectl delete namespace $namespace

# 3. Recreate the namespace
kubectl create namespace $namespace

# 4. Build umbrella chart dependencies
cd helm/brzina
helm dependency build
cd ../..

# 5. Install/upgrade the full brzina stack
helm upgrade --install brzina helm/brzina -n $namespace

Write-Host "\nSetup complete. Check pod and service status with: kubectl get pods,svc -n brzina"
