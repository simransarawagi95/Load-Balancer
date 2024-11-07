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

# ConfigMap name and namespace
CONFIGMAP_NAME = "healthy-pods-configmap"


def check_health(pod_ip):
    """Check the health of the pod."""
    try:
        response = requests.get(f"http://{pod_ip}:3000/health", timeout=2)
        print(f"Checking health for pod at {pod_ip}: Status code {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error checking health for pod at {pod_ip}: {e}")
        return False
    
def get_healthy_pods():

    healthy_pods_cache = {}

    for service in SERVICES:
        service_name = service["name"]
        label_selector = f"app={service['label']}"
        healthy_pods = []
        
        # Get all pods with the specified label
        pods = v1.list_namespaced_pod(NAMESPACE, label_selector=label_selector).items
        
        for pod in pods:
            pod_ip = pod.status.pod_ip
            if pod.status.phase == "Running" and check_health(pod_ip):
                healthy_pods.append(pod_ip)
        
        healthy_pods_cache[service_name] = healthy_pods

    return healthy_pods_cache


def update_configmap(healthy_pods):
    """Update the ConfigMap with healthy pods."""
    cm = v1.read_namespaced_config_map(CONFIGMAP_NAME, NAMESPACE)
    cm.data['healthy_pods'] = str(healthy_pods)  # Update the ConfigMap with the healthy pod data
    v1.replace_namespaced_config_map(CONFIGMAP_NAME, NAMESPACE, cm)
    print("Updated ConfigMap with healthy pods.")



def monitor_health():
    while True:
        healthy_pods = get_healthy_pods()
        update_configmap(healthy_pods)
        time.sleep(60)
        # get_healthy_pods()

if __name__ == "__main__":
    monitor_health()
