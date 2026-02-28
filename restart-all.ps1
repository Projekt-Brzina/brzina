# PowerShell script to restart all deployments in the brzina namespace
$deployments = kubectl get deployments -n brzina -o jsonpath="{.items[*].metadata.name}"
foreach ($d in $deployments.Split(" ")) {
    kubectl rollout restart deployment $d -n brzina
}
Write-Host "All deployments restarted in namespace brzina."
