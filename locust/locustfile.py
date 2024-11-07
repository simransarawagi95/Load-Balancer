import logging
import time
from locust import HttpUser, task, between
from kubernetes import client, config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ConfigMap details
NAMESPACE = "default"
CONFIGMAP_NAME = "healthy-pods-configmap"

# Round-robin index to track the current pod to send traffic to
pod_index = {}
last_refresh_time = 0
refresh_interval = 10  # seconds to wait before re-reading the ConfigMap

# Kubernetes API client setup
config.load_incluster_config()  # Use this if running inside a Kubernetes cluster
v1 = client.CoreV1Api()

# Fetch healthy pods from the ConfigMap
def get_healthy_pods_from_configmap():
    """Get the healthy pods from the ConfigMap."""
    cm = v1.read_namespaced_config_map(CONFIGMAP_NAME, NAMESPACE)
    healthy_pods_str = cm.data.get("healthy_pods", "[]")
    try:
        healthy_pods = eval(healthy_pods_str)  # Convert string to dictionary
    except Exception as e:
        # logger.error(f"Error parsing ConfigMap data: {e}")
        healthy_pods = {}
    return healthy_pods

# Initialize the round-robin indices for each service
def initialize_pod_index(healthy_pods):
    """Initialize the round-robin index for each service."""
    for service, pods in healthy_pods.items():
        pod_index[service] = 0

# Locust user class
class LoadTest(HttpUser):
    wait_time = between(1, 5)  # Adjust the time between requests

    def on_start(self):
        """Fetch healthy pods and initialize the round-robin index."""
        self.healthy_pods = get_healthy_pods_from_configmap()
        initialize_pod_index(self.healthy_pods)
    
    def refresh_healthy_pods(self):
        """Refresh healthy pods from the ConfigMap periodically."""
        global last_refresh_time
        if time.time() - last_refresh_time > refresh_interval:
            logger.info("Refreshing healthy pods from ConfigMap.")
            self.healthy_pods = get_healthy_pods_from_configmap()
            initialize_pod_index(self.healthy_pods)
            last_refresh_time = time.time()

    def get_next_healthy_pod(self, service_name):
        """Get the next healthy pod for the specified service using round-robin."""
        if service_name not in self.healthy_pods or not self.healthy_pods[service_name]:
            # logger.warning(f"No healthy pods available for {service_name}")
            return None

        # Get the current pod index for round-robin distribution
        index = pod_index.get(service_name, 0)
        pod_ip = self.healthy_pods[service_name][index]

        # Update the round-robin index
        pod_index[service_name] = (index + 1) % len(self.healthy_pods[service_name])

        return pod_ip

    @task
    def send_traffic(self):
        """Send traffic to the healthy pods using round-robin."""
        self.refresh_healthy_pods()
        for service in ["node-app-primary-service", "node-app-secondary-service", "node-app-failover-service"]:
            pod_ip = self.get_next_healthy_pod(service)
            if pod_ip:
                url = f"http://{pod_ip}:3000"
                logger.info(f"Sending traffic to service: {service} at {url}")
                self.client.get(url)
                break
            else:
                logger.warning(f"No healthy pods available for service {service}. Skipping traffic distribution.")

