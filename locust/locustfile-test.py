import random
import logging
import requests
from locust import HttpUser, task, between

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoadTest(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        # logger.info("Starting load test...")
        # Fetch healthy pods from the health checker
        self.healthy_pods = self.get_healthy_pods()

    # def get_next_healthy_pod(self, service_name):
    #     """Fetch the next healthy pod for the specified service from the health checker."""
    #     response = requests.get(f"http://health-checker.default.svc.cluster.local:8080/next-healthy-pod", params={"service": service_name})
    #     if response.status_code == 200:
    #         # logger.info(f"Next healthy pod for {service_name} fetched successfully.")
    #         return response.json().get("pod_ip")
    #     else:
    #         # logger.error(f"Failed to fetch next healthy pod for {service_name}. Status code: {response.status_code}")
    #         return None

    def get_healthy_pods(self):
        """Fetch healthy pods from the health check service."""
        logger.info("Fetching healthy pods...")
        response = requests.get("http://health-checker.default.svc.cluster.local:8080/health-pods")
        if response.status_code == 200:
            logger.info("Healthy pods fetched successfully.")
            return response.json()
        else:
            logger.error(f"Failed to fetch healthy pods. Status code: {response.status_code}")
            return {}

    @task
    def send_traffic(self):
        """Send traffic to the healthy pods."""
        if not self.healthy_pods:
            logger.info("No healthy pods available. Fetching again...")
            self.healthy_pods = self.get_healthy_pods()  # Re-fetch if the list is empty

        if not self.healthy_pods:
            logger.error("No healthy pods found. Skipping traffic generation.")
            return

        # Choose a healthy service to send traffic to
        for service, pods in self.healthy_pods.items():
            if pods:
                pod_ip = random.choice(pods)  # Randomly pick a healthy pod
                url = f"http://{pod_ip}:3000"
                # logger.info(f"Sending traffic to pod: {url}")
                logger.info(f"Sending traffic to service: {service}")
                self.client.get(url)
                break
            else:
                logger.warning(f"No healthy pods found for service {service}.")

    # @task
    # def send_traffic(self):
    #     """Send traffic to the healthy pods using round-robin."""
    #     for service in ["node-app-primary-service", "node-app-secondary-service", "node-app-failover-service"]:
    #         pod_ip = self.get_next_healthy_pod(service)
    #         if pod_ip:
    #             url = f"http://{pod_ip}:3000"
    #             # logger.info(f"Sending traffic to pod: {url}")
    #             logger.info(f"Sending traffic to service: {service}")
    #             self.client.get(url)
                # break
    #         # else:
    #             # logger.warning(f"No healthy pods available for service {service}.")

