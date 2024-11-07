import time
import requests
from kubernetes import client, config

# Load Kubernetes configuration
config.load_incluster_config()  # Use this if running inside a cluster

# Define the app labels (not the service names)
SERVICES = [
    {"name": "node-app-primary-service", "label": "node-app-primary"},
    {"name": "node-app-secondary-service", "label": "node-app-secondary"},
    {"name": "node-app-failover-service", "label": "node-app-failover"}
]
NAMESPACE = "default"  # Change this to your namespace

# Kubernetes API client
v1 = client.CoreV1Api()


def check_health(pod_ip):
    """Check the health of the pod."""
    try:
        response = requests.get(f"http://{pod_ip}:3000/health", timeout=2)
        print(f"Checking health for pod at {pod_ip}: Status code {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error checking health for pod at {pod_ip}: {e}")
        return False   

def update_service_endpoints(service_name, healthy_pods):
    """Update the service endpoint with healthy pods."""
    endpoints = v1.read_namespaced_endpoints(service_name, NAMESPACE)

    # Prepare new endpoints
    new_subsets = []
    if healthy_pods:
        new_subsets.append(client.V1EndpointSubset(
            addresses=[client.V1EndpointAddress(ip=ip) for ip in healthy_pods]
        ))
    # New
    else:
        # No healthy pods, remove the endpoint entirely or ensure no addresses are present
        print(f"No healthy pods for {service_name}. Removing endpoints.")
        new_subsets = []

    # Update endpoints with the healthy pods
    endpoints.subsets = new_subsets
    v1.patch_namespaced_endpoints(service_name, NAMESPACE, endpoints)
    print(f"Updated {service_name} endpoints: {healthy_pods if healthy_pods else 'No healthy pods available'}")



def monitor_health():
    while True:
        for service in SERVICES:
            service_name = service["name"]
            label_selector = f"app={service['label']}"
            healthy_pods = []
            
            # Get all pods with the specified label
            pods = v1.list_namespaced_pod(NAMESPACE, label_selector=label_selector).items
            
            for pod in pods:
                pod_ip = pod.status.pod_ip
                if pod.status.phase == "Running":
                    print(f"Pod {pod.metadata.name} in {service_name} has IP {pod_ip} and is in 'Running' phase.")
                    if check_health(pod_ip):
                        print(f"Pod {pod.metadata.name} in {service_name} is healthy.")
                        healthy_pods.append(pod_ip)
                    else:
                        print(f"Pod {pod.metadata.name} in {service_name} is unhealthy.")
                else:
                    print(f"Pod {pod.metadata.name} in {service_name} is not in 'Running' phase. Current phase: {pod.status.phase}")

            # Only update the endpoints if there are healthy pods
            if healthy_pods:
                update_service_endpoints(service_name, healthy_pods)
            else:
                print(f"No healthy pods for {service_name}.")

        time.sleep(3)  # Wait before the next check

if __name__ == "__main__":
    try:
        monitor_health()
    except KeyboardInterrupt:
        print("Health check monitoring stopped.")
