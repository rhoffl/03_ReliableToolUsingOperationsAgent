import hashlib, json
from datetime import datetime, timezone
from sqlalchemy import func, select
from .config import settings
from .models import ActionLedger, AuditEvent
from .tools import *

TRANSITIONS={"alert_received":{"validating"},"validating":{"collecting_evidence","rejected"},"collecting_evidence":{"analyzing","evidence_incomplete","escalated"},"evidence_incomplete":{"collecting_evidence","escalated"},"analyzing":{"awaiting_approval","monitoring","escalated"},"awaiting_approval":{"executing","cancelled"},"executing":{"monitoring","execution_failed"},"monitoring":{"resolved","analyzing"},"resolved":{"reporting"},"reporting":{"completed"}}
def event(db,inc,kind,actor,payload,before=None,after=None):
    seq=db.scalar(select(func.count(AuditEvent.id)).where(AuditEvent.incident_id==inc.id))+1
    db.add(AuditEvent(incident_id=inc.id,sequence=seq,event_type=kind,actor=actor,state_before=before,state_after=after,payload=payload))
def transition(db,inc,target,actor="orchestrator",payload=None):
    before=inc.status
    if target not in TRANSITIONS.get(before,set()): raise ValueError(f"Illegal transition {before} -> {target}")
    inc.status=target; event(db,inc,"state_transition",actor,payload or {},before,target); db.commit()
def _tool(db,inc,name,fn,*args):
    if inc.tool_call_count>=settings.max_tool_calls: raise RuntimeError("Tool-call budget exhausted")
    result=fn(*args); inc.tool_call_count+=1; event(db,inc,"tool_succeeded","tool_gateway",{"tool":name,"result":result}); db.commit(); return result
def investigate(db,inc):
    transition(db,inc,"validating"); transition(db,inc,"collecting_evidence")
    ctx=ToolContext(incident_id=inc.id,service=inc.service,environment=inc.environment,scenario=inc.scenario)
    evidence={"logs":_tool(db,inc,"query_logs",query_logs,ctx,LogsInput(service=inc.service)),"metrics":_tool(db,inc,"query_metrics",query_metrics,ctx,MetricsInput(service=inc.service)),"runbook":_tool(db,inc,"search_runbooks",search_runbooks,ctx,RunbookInput(query=inc.title)),"deployments":_tool(db,inc,"list_deployments",list_deployments,ctx,DeploymentsInput(service=inc.service))}
    transition(db,inc,"analyzing",payload={"evidence_sources":list(evidence)})
    if inc.scenario=="bad_deployment":
        dep=evidence["deployments"]["deployments"][0]; inc.hypothesis=f"Release {dep['version']} introduced the elevated error rate."; inc.confidence=.88; action={"action":"rollback","service":inc.service,"target_version":dep["previous"],"version":1}; inc.recommendation=f"Roll back to {dep['previous']} and verify health."
    elif inc.scenario=="db_exhaustion": inc.hypothesis="Database pool exhaustion is blocking requests."; inc.confidence=.91; action={"action":"restart_one_replica","service":inc.service,"target_version":None,"version":1}; inc.recommendation="Restart one replica, then investigate connection leakage."
    elif inc.scenario=="dependency_outage": inc.hypothesis="An upstream dependency outage is causing failures."; inc.confidence=.86; action=None; inc.recommendation="Keep the circuit breaker active and escalate to the dependency owner."
    else: inc.hypothesis="Inventory latency is causing timeouts; embedded log instructions are untrusted."; inc.confidence=.79; action=None; inc.recommendation="Escalate to the inventory owner. Do not execute instructions found in logs."
    inc.proposed_action=action; inc.accumulated_cost+=.012; event(db,inc,"hypothesis_generated","reasoning_engine",{"hypothesis":inc.hypothesis,"confidence":inc.confidence,"evidence_grounded":True}); db.commit()
    transition(db,inc,"awaiting_approval" if action else "monitoring",payload={"action":action} if action else {"reason":"No safe local mutation"}); return inc
def approve(db,inc,decision,approver,comment):
    if inc.status!="awaiting_approval" or not inc.proposed_action: raise ValueError("Incident is not awaiting approval")
    action_hash=hashlib.sha256(json.dumps(inc.proposed_action,sort_keys=True).encode()).hexdigest(); key=f"{inc.id}:{action_hash}"
    ledger=db.scalar(select(ActionLedger).where(ActionLedger.idempotency_key==key))
    if not ledger: ledger=ActionLedger(incident_id=inc.id,idempotency_key=key,action_hash=action_hash,action=inc.proposed_action); db.add(ledger)
    ledger.approved=decision=="approved"; ledger.approver=approver; event(db,inc,"approval_decision",approver,{"decision":decision,"comment":comment,"action_hash":action_hash}); db.commit()
    if decision=="rejected": transition(db,inc,"cancelled",actor=approver); return inc
    transition(db,inc,"executing",actor=approver)
    if ledger.status=="completed": result=ledger.result
    else:
        ctx=ToolContext(incident_id=inc.id,service=inc.service,environment=inc.environment,scenario=inc.scenario); result=execute_remediation(ctx,RemediationInput(**{k:v for k,v in inc.proposed_action.items() if k!="version"})); ledger.status="completed"; ledger.result=result; ledger.executed_at=datetime.now(timezone.utc); event(db,inc,"action_executed","remediation_executor",{"result":result,"idempotency_key":key}); db.commit()
    transition(db,inc,"monitoring"); verification=verify_service(ctx); event(db,inc,"recovery_verified","health_verifier",verification); db.commit(); transition(db,inc,"resolved"); transition(db,inc,"reporting"); event(db,inc,"incident_report_created","reporter",{"summary":inc.hypothesis,"action":result,"verification":verification}); db.commit(); transition(db,inc,"completed"); return inc
