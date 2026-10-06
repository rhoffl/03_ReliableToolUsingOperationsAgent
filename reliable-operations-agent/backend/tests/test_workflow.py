def create(client,scenario="bad_deployment"):
    return client.post("/api/incidents",json={"title":"Checkout error spike","service":"checkout-api","environment":"production","severity":"SEV1","scenario":scenario}).json()
def test_approval_gated_workflow(client):
    inc=create(client); investigated=client.post(f"/api/incidents/{inc['id']}/investigate").json(); assert investigated["status"]=="awaiting_approval"; assert investigated["tool_call_count"]==4
    done=client.post(f"/api/incidents/{inc['id']}/approval",json={"decision":"approved","approver":"oncall@example.com"}).json(); assert done["status"]=="completed"
    assert any(e["event_type"]=="recovery_verified" for e in client.get(f"/api/incidents/{inc['id']}/events").json())
def test_prompt_injection_is_inert(client):
    inc=create(client,"prompt_injection"); out=client.post(f"/api/incidents/{inc['id']}/investigate").json(); assert out["status"]=="monitoring"; assert out["proposed_action"] is None; assert "untrusted" in out["hypothesis"]
def test_rejection_cancels(client):
    inc=create(client); client.post(f"/api/incidents/{inc['id']}/investigate"); out=client.post(f"/api/incidents/{inc['id']}/approval",json={"decision":"rejected","approver":"lead@example.com"}).json(); assert out["status"]=="cancelled"
