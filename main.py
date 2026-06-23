import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, HttpUrl
from k8s_manager import K8sManager
from smoke_tester import run_smoke_test
from report_generator import generate_pdf_report
from notifier import send_whatsapp_alert

# Setup structured core logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DeployShield.Core")

app = FastAPI(
    title="DeployShield Gateway",
    version="1.0.0",
    description="Automated Kubernetes Rollout Guard & Canary Validation Webhook Engine"
)

# Initialize our cluster management layer
try:
    k8s = K8sManager()
except Exception as e:
    logger.error(f"Critical System Fault: Orchestration engine failed to attach to cluster: {e}")
    k8s = None

class DeploymentWebhook(BaseModel):
    namespace: str = "default"
    deployment_name: str
    image_tag: str
    smoke_test_url: HttpUrl
    phone_number: str

def orchestration_guard_worker(data: DeploymentWebhook):
    """
    Asynchronous background lifecycle worker monitoring rollout state transitions,
    running service assertions, and handling rollbacks on failure.
    """
    logger.info(f"Background thread tracking active for target: {data.deployment_name}")
    
    # Stage 1: Monitor cluster deployment rollout status
    rollout_success = k8s.wait_for_rollout(
        namespace=data.namespace, 
        deployment_name=data.deployment_name
    )
    
    smoke_success = False
    smoke_msg = "Skipped (Rollout Phase Failed)"
    rollout_status_str = "Passed" if rollout_success else "Failed (Terminal State or Timeout)"
    
    # Stage 2: Execute Canary Smoke Assertions if rollout succeeded
    if rollout_success:
        logger.info("Deployment rollout check succeeded. Initiating smoke testing phase...")
        smoke_success, status_code, reason = run_smoke_test(str(data.smoke_test_url))
        smoke_msg = f"Passed (HTTP {status_code})" if smoke_success else f"Failed (HTTP {status_code}: {reason})"
    else:
        logger.warning("Deployment anomaly verified during cluster rollout stage!")

    # Stage 3: Mitigate & Remediate Anomalies if any checks fail
    if not rollout_success or not smoke_success:
        logger.error(f"Anomaly Confirmed on '{data.deployment_name}'. Initiating rollback sequence...")
        
        # Pull diagnostic logs/events before state is completely wiped
        error_logs = k8s.fetch_failed_pod_logs(
            namespace=data.namespace, 
            deployment_name=data.deployment_name
        )
        
        # Trigger rolling emergency patch back to previous ReplicaSet
        rollback_triggered = k8s.trigger_rollback(
            namespace=data.namespace, 
            deployment_name=data.deployment_name
        )
        
        rollout_status_str += f" | Automated Rollback: {'Executed' if rollback_triggered else 'Failed'}"
        
        # Compile local analytical incident artifact PDF
        report_path = generate_pdf_report(
            deployment_name=data.deployment_name,
            namespace=data.namespace,
            image_tag=data.image_tag,
            rollout_status=rollout_status_str,
            smoke_status=smoke_msg,
            error_logs=error_logs
        )
        logger.info(f"Incident report generated locally: {report_path}")
        
        # Alert engineering team via notification channel
        send_whatsapp_alert(
            to_number=data.phone_number,
            deployment_name=data.deployment_name,
            status="FAILED",
            report_path=report_path
        )
    else:
        # Ultimate Success State reached
        logger.info(f"Deployment target '{data.deployment_name}' verified completely healthy. Closing pipeline scope.")
        send_whatsapp_alert(
            to_number=data.phone_number,
            deployment_name=data.deployment_name,
            status="SUCCESS"
        )

@app.post("/v1/deploy/watch", status_code=status.HTTP_202_ACCEPTED)
async def watch_deployment(payload: DeploymentWebhook, background_tasks: BackgroundTasks):
    """
    Accepts deployment telemetry manifests and hands off tracking execution tasks
    instantly to background worker queues.
    """
    if not k8s:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kubernetes client subsystem is uninitialized or disconnected from cluster context."
        )
        
    background_tasks.add_task(orchestration_guard_worker, payload)
    return {
        "status": "Accepted",
        "message": f"Deployment tracking workflow spawned for '{payload.deployment_name}' in namespace '{payload.namespace}'."
    }

@app.get("/healthz", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy", "cluster_connected": k8s is not None}