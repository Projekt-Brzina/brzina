# NGINX Ingress Controller: Upgrade, Patch, and Restart Snippets
# --------------------------------------------------------------

# 1. Upgrade the nginx ingress controller to a specific version (replace version as needed)
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.10.1/deploy/static/provider/cloud/deploy.yaml

# 2. Patch the controller deployment to add or update the default backend argument
kubectl -n ingress-nginx patch deployment ingress-nginx-controller \
  --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--default-backend-service=brzina/default-backend"}]'
# (If the argument already exists, use "replace" instead of "add" in the op field.)

# 3. Restart the ingress controller pods (forces them to reload config)
kubectl delete pod -l app.kubernetes.io/name=ingress-nginx -n ingress-nginx

# 4. Check status of ingress controller and resources
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
kubectl get ingress -A

# 5. (Optional) Edit the deployment manually in your editor
kubectl -n ingress-nginx edit deployment ingress-nginx-controller

# 6. (Optional) Roll back to a previous deployment revision
kubectl -n ingress-nginx rollout undo deployment ingress-nginx-controller

# 7. (Optional) View logs for troubleshooting
tail -f <(kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx --all-containers)
# Or for a specific pod:
kubectl logs <pod-name> -n ingress-nginx
