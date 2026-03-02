# 1. Create Kind cluster
kind create cluster --config infra/kind/kind-config.yaml

# 2. Build Docker images
docker build --no-cache -t brzina-api:latest services/api
docker build --no-cache -t brzina-auth:latest services/auth
docker build --no-cache -t brzina-booking:latest services/booking
docker build --no-cache -t brzina-car:latest services/car
docker build --no-cache -t brzina-payment:latest services/payment
docker build --no-cache -t brzina-frontend:latest frontend

# 3. Load images into Kind
kind load docker-image brzina-api:latest
kind load docker-image brzina-auth:latest
kind load docker-image brzina-booking:latest
kind load docker-image brzina-car:latest
kind load docker-image brzina-payment:latest
kind load docker-image brzina-frontend:latest


kubectl create namespace brzina
kubectl config set-context --current --namespace=brzina


# 4. Deploy PostgreSQL
kubectl create configmap postgres-initdb --from-file=infra/db/init.sql -n brzina
kubectl apply -f infra/k8s/postgres/

# 5. Deploy backend and frontend with Helm
helm install api helm/api
helm install auth helm/auth
helm install booking helm/booking
helm install car helm/car
helm install payment helm/payment
helm install frontend helm/frontend

helm upgrade --install api helm/api -n brzina --set image.pullPolicy=Always
helm upgrade --install auth helm/auth -n brzina --set image.pullPolicy=Always
helm upgrade --install booking helm/booking -n brzina --set image.pullPolicy=Always
helm upgrade --install car helm/car -n brzina --set image.pullPolicy=Always
helm upgrade --install payment helm/payment -n brzina --set image.pullPolicy=Always
helm upgrade --install frontend helm/frontend -n brzina --set image.pullPolicy=Always
helm upgrade --install kafka helm/kafka -n brzina --set image.pullPolicy=Always

helm upgrade --install auth helm/auth -n brzina --set image.pullPolicy=Always

helm upgrade --install brzina helm/brzina -n brzina

kubectl run -it --rm debug --image=alpine --restart=Never -n brzina -- sh

# 6. Deploy ingress controller and ingress
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.10.1/deploy/static/provider/cloud/deploy.yaml
kubectl apply -f infra/k8s/ingress.yaml --namespace=ingress-nginx
kubectl apply -f infra/k8s/default-backend.yaml

# 7. Show status
kubectl get pods,svc,deployments

Write-Host "Deployment complete! Check your ingress address and open the frontend in your browser."
kubectl run -it --rm debug --image=alpine --restart=Never -n brzina -- sh


kubectl delete pod -l app=api -n brzina
kubectl delete pod -l app=auth -n brzina
kubectl delete pod -l app=booking -n brzina
kubectl delete pod -l app=car -n brzina
kubectl delete pod -l app=payment -n brzina
kubectl delete pod -l app=frontend -n brzina

Invoke-WebRequest -H 
"Authorization: Bearer <>" 
-d '{"brand":"eet","hourly_rate":3, "model": "rwe", "plate": 123123, "tenant_id":1}'  -v http://car-car:8000/cars/

"Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidGVuYW50X2lkIjoxLCJleHAiOjE3NzI0MDE3MjB9.Dpbfnr63MujcI7heMnTmkwRxYqqMELm40eSMy4csNmM"


