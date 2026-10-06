from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from .config import settings
from .db import Base, engine, get_db
from .models import AuditEvent, Incident
from .schemas import ApprovalRequest, EventOut, IncidentCreate, IncidentOut
from .workflow import approve, event, investigate

app=FastAPI(title="Reliable Operations Agent",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins.split(","),allow_methods=["*"],allow_headers=["*"])
@app.on_event("startup")
def startup(): Base.metadata.create_all(engine)
@app.get("/health")
def health(): return {"status":"ok"}
@app.get("/api/incidents",response_model=list[IncidentOut])
def list_incidents(db=Depends(get_db)): return db.scalars(select(Incident).order_by(Incident.created_at.desc())).all()
@app.post("/api/incidents",response_model=IncidentOut,status_code=201)
def create_incident(body:IncidentCreate,db=Depends(get_db)):
    inc=Incident(**body.model_dump()); db.add(inc); db.flush(); event(db,inc,"alert_received","alert_gateway",body.model_dump()); db.commit(); db.refresh(inc); return inc
@app.get("/api/incidents/{incident_id}",response_model=IncidentOut)
def get_incident(incident_id:str,db=Depends(get_db)):
    inc=db.get(Incident,incident_id)
    if not inc: raise HTTPException(404,"Incident not found")
    return inc
@app.post("/api/incidents/{incident_id}/investigate",response_model=IncidentOut)
def run_investigation(incident_id:str,db=Depends(get_db)):
    inc=db.get(Incident,incident_id)
    if not inc: raise HTTPException(404,"Incident not found")
    if inc.status!="alert_received": raise HTTPException(409,"Investigation already started")
    try: return investigate(db,inc)
    except Exception as exc: db.rollback(); raise HTTPException(500,f"Investigation failed: {exc}")
@app.post("/api/incidents/{incident_id}/approval",response_model=IncidentOut)
def approval(incident_id:str,body:ApprovalRequest,db=Depends(get_db)):
    inc=db.get(Incident,incident_id)
    if not inc: raise HTTPException(404,"Incident not found")
    try: return approve(db,inc,body.decision,body.approver,body.comment)
    except ValueError as exc: raise HTTPException(409,str(exc))
@app.get("/api/incidents/{incident_id}/events",response_model=list[EventOut])
def events(incident_id:str,db=Depends(get_db)): return db.scalars(select(AuditEvent).where(AuditEvent.incident_id==incident_id).order_by(AuditEvent.sequence)).all()
