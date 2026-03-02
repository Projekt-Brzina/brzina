# Wait for all pods in brzina namespace to be ready
Write-Host "Waiting for all pods in 'brzina' namespace to be ready..."
while ((kubectl get pods -n brzina --no-headers | Select-String -Pattern '0/\d+|ContainerCreating|Pending|CrashLoopBackOff|Error')) {
    Start-Sleep -Seconds 2
}
Write-Host "All pods in 'brzina' namespace are ready."

# Wait for ingress-nginx controller pod to be ready
Write-Host "Waiting for nginx ingress controller pod to be ready..."
while ((kubectl get pods -n ingress-nginx --no-headers | Select-String -Pattern '0/\d+|ContainerCreating|Pending|CrashLoopBackOff|Error')) {
    Start-Sleep -Seconds 2
}
Write-Host "nginx ingress controller pod is ready."

# Apply ingress and default backend
kubectl apply -f infra/k8s/ingress.yaml
kubectl apply -f infra/k8s/default-backend.yaml

# Show status
kubectl get pods,svc,deployments -n brzina
kubectl get pods -n ingress-nginx
kubectl get ingress -n brzina

Write-Host "Ingress and default backend applied. Test unmatched routes for the custom message."
kubectl delete pod -l app.kubernetes.io/name=ingress-nginx -n ingress-nginx