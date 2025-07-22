# LangGraph Kubernetes Cluster Setup for 5000 Concurrent Users

## Prerequisites
- Kubernetes cluster (GKE, EKS, or AKS recommended)
- kubectl configured
- Helm 3.x installed
- Minimum cluster resources: 32 CPUs, 64GB RAM

## Step 1: Install KEDA (Event-driven Autoscaling)
```bash
# Add KEDA repository
helm repo add kedacore https://kedacore.github.io/charts
helm install keda kedacore/keda --namespace keda --create-namespace

# Verify KEDA installation
kubectl get pods -n keda
```

## Step 2: Verify Storage Classes
```bash
# Check for dynamic provisioners
kubectl get storageclass

# You should see something like:
# NAME                 PROVISIONER
# standard (default)   kubernetes.io/gce-pd
```

## Step 3: Configure Network Egress
Ensure your cluster can reach:
- https://api.host.langchain.com
- https://api.smith.langchain.com

## Step 4: Create Dedicated Namespace
```bash
kubectl create namespace langgraph-production
kubectl config set-context --current --namespace=langgraph-production
``` 