import time
import requests
from kubernetes import client, config
from flask import Flask, jsonify, request

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


app = Flask(__name__)
healthy_pods_cache = {}

pod_index = {service["name"]: 0 for service in SERVICES}  # Initialize round-robin index

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
    global healthy_pods_cache
    if healthy_pods_cache:
        return healthy_pods_cache

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

@app.route("/health-pods", methods=["GET"])
def health_pods():
    """API endpoint to get healthy pods."""
    return jsonify(get_healthy_pods())


@app.route("/next-healthy-pod", methods=["GET"])
def next_healthy_pod():
    """API endpoint to get the next healthy pod based on round-robin for a specified service."""
    service_name = request.args.get("service")
    healthy_pods = get_healthy_pods().get(service_name, [])

    if not healthy_pods:
        return jsonify({"error": f"No healthy pods available for service {service_name}"}), 404

    # Get the next pod in round-robin order
    index = pod_index[service_name]
    pod_ip = healthy_pods[index]
    pod_index[service_name] = (index + 1) % len(healthy_pods)  # Update index

    return jsonify({"pod_ip": pod_ip})


def monitor_health():
    while True:
        get_healthy_pods()
        time.sleep(3)  # Wait before the next check

if __name__ == "__main__":
    # Start health monitoring in the background
    import threading
    threading.Thread(target=monitor_health, daemon=True).start()
    
    # Start Flask API
    app.run(host="0.0.0.0", port=8080)
