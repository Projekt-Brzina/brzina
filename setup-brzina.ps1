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


# 4. Build umbrella chart dependencies (always remove Chart.lock to avoid sync errors)
cd helm/brzina
if (Test-Path Chart.lock) { Remove-Item Chart.lock }
helm dependency build
cd ../..


# 5. Install/upgrade the full brzina stack (including nginx-ingress)
helm upgrade --install brzina helm/brzina -n $namespace

# 6. Wait for nginx-ingress-controller pod to be ready (max 3 minutes)
$waitTime = 0
$maxWait = 60
while ($waitTime -lt $maxWait) {
    $pod = kubectl get pods -n $namespace -l app.kubernetes.io/component=controller,app.kubernetes.io/instance=brzina-nginx-ingress -o json | ConvertFrom-Json
    if ($pod.items.Count -gt 0 -and $pod.items[0].status.phase -eq "Running" -and $pod.items[0].status.containerStatuses[0].ready) {
        Write-Host "nginx-ingress-controller is ready."
        break
    }
    Start-Sleep -Seconds 5
    $waitTime += 5
    if ($waitTime -ge $maxWait) {
        Write-Host "Timeout waiting for nginx-ingress-controller to be ready."
    }
}

Write-Host "\nSetup complete. Check pod and service status with: kubectl get pods,svc -n brzina"
