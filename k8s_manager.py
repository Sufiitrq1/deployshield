import time
import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DeployShield.K8sManager")

class K8sManager:
    def __init__(self):
        # Load configuration from local kubeconfig (Minikube context)
        try:
            config.load_kube_config()
            self.apps_v1 = client.AppsV1Api()
            self.core_v1 = client.CoreV1Api()
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise e

    def wait_for_rollout(self, namespace: str, deployment_name: str, timeout: int = 120) -> bool:
        """Polls the cluster to check if the rollout succeeds or hits a terminal failure."""
        logger.info(f"Initiating guard loop tracking for deployment: '{deployment_name}'")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # 1. Fetch deployment status
                dep = self.apps_v1.read_namespaced_deployment_status(name=deployment_name, namespace=namespace)
                status = dep.status
                spec = dep.spec
                
                # Align status fields with desired replica configurations
                replicas = status.replicas or 0
                updated_replicas = status.updated_replicas or 0
                ready_replicas = status.ready_replicas or 0
                available_replicas = status.available_replicas or 0
                
                logger.info(f"Tracking [{deployment_name}] -> Target: {spec.replicas} | Updated: {updated_replicas} | Ready: {ready_replicas}")
                
                # Check for successful rollout completion
                if (updated_replicas == spec.replicas and 
                    ready_replicas == spec.replicas and 
                    available_replicas == spec.replicas and 
                    status.observed_generation >= dep.metadata.generation):
                    return True
                
                # 2. Inspect active pods for terminal failure states
                label_selector = ",".join([f"{k}={v}" for k, v in spec.selector.match_labels.items()])
                pods = self.core_v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector)
                
                for pod in pods.items:
                    # FIX: Access container_statuses safely via the pod.status object path layout
                    if pod.status and pod.status.container_statuses:
                        for container_status in pod.status.container_statuses:
                            state = container_status.state
                            if state and state.waiting:
                                reason = state.waiting.reason
                                # Intercept known unrecoverable deployment errors
                                if reason in ["CrashLoopBackOff", "ImagePullBackOff", "ErrImagePull", "CreateContainerConfigError"]:
                                    logger.error(f"Terminal pod error state discovered: {reason}")
                                    return False
                                
            except ApiException as e:
                logger.warning(f"K8s API query hiccup: {e.reason}")
                
            time.sleep(5)
            
        logger.warning(f"Deployment rollout tracking timed out after {timeout} seconds.")
        return False

    def trigger_rollback(self, namespace: str, deployment_name: str) -> bool:
        """Reverts deployment template back to match the previously configured ReplicaSet layout."""
        logger.info(f"Executing emergency rollback sequence for '{deployment_name}'")
        try:
            dep = self.apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
            label_selector = ",".join([f"{k}={v}" for k, v in dep.spec.selector.match_labels.items()])
            
            # Find matching ReplicaSets to track version lineage
            replica_sets = self.apps_v1.list_namespaced_replica_set(namespace=namespace, label_selector=label_selector)
            
            # Sort ReplicaSets dynamically by their revision numbers descending
            sorted_rs = sorted(
                [rs for rs in replica_sets.items if rs.metadata.annotations and rs.metadata.annotations.get("deployment.kubernetes.io/revision")],
                key=lambda x: int(x.metadata.annotations["deployment.kubernetes.io/revision"]),
                reverse=True
            )
            
            if len(sorted_rs) < 2:
                logger.error("Rollback aborted: No historical validation target (previous ReplicaSet) found.")
                return False
                
            # target the second most recent history array element (Index 1)
            previous_rs = sorted_rs[1]
            logger.info(f"Restoring layout to revision target: #{previous_rs.metadata.annotations['deployment.kubernetes.io/revision']}")
            
            # Patch deployment spec to match previous stable state
            dep.spec.template = previous_rs.spec.template
            self.apps_v1.patch_namespaced_deployment(name=deployment_name, namespace=namespace, body=dep)
            return True
            
        except ApiException as e:
            logger.error(f"Critical operational fault executing fallback patching: {e.reason}")
            return False

    def fetch_failed_pod_logs(self, namespace: str, deployment_name: str) -> str:
        """Extracts debug logs from failing pods, falling back to core events if containers can't start."""
        try:
            dep = self.apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
            label_selector = ",".join([f"{k}={v}" for k, v in dep.spec.selector.match_labels.items()])
            pods = self.core_v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector)
            
            if not pods.items:
                return "No pods associated with deployment discovered."
                
            target_pod = pods.items[0]
            pod_name = target_pod.metadata.name
            
            # Determine if pod failed before container runtime initialization
            is_pull_failure = False
            if target_pod.status and target_pod.status.container_statuses:
                for status in target_pod.status.container_statuses:
                    if status.state and status.state.waiting and status.state.waiting.reason in ["ImagePullBackOff", "ErrImagePull"]:
                        is_pull_failure = True
                        break
                        
            if is_pull_failure:
                # Fetch platform event context logs instead of standard stdout streams
                events = self.core_v1.list_namespaced_event(namespace=namespace, field_selector=f"involvedObject.name={pod_name}")
                event_logs = [f"[{e.type}] {e.reason}: {e.message}" for e in events.items]
                return "\n".join(event_logs[-20:]) if event_logs else "Image pull failure occurred but no infrastructure events were registered."
            
            # Default lookup to active runtime container stdout streams
            return self.core_v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, tail_lines=50)
            
        except Exception as e:
            return f"Failed to acquire operational trace logs from cluster: {str(e)}"