"""
Server-enforced agent ↔ arena binding (ROADMAP §2.1 D1 / ADR-0005).

The orchestrator — not just the gateway — gates whether an `agent` key may DRIVE
an arena (exec / report findings / configure the victim), and in what stance.
Operators/admins manage every arena and bypass the check. Bindings are granted
three ways: auto on agent self-deploy (own sandbox), an operator grant, or named
at setup/start (configurator, revoked at finish).
"""
import base64

import pytest
from fastapi.testclient import TestClient


def _client(role, name):
    import api
    import auth
    from database import Database

    key = auth.generate_api_key()
    Database().create_api_key(auth.hash_api_key(key), name=name, role=role)
    c = TestClient(api.app)
    c.headers["X-API-Key"] = key
    c.db = Database()
    c.principal_name = name
    return c


@pytest.fixture()
def operator():
    return _client("operator", "binding-op")


@pytest.fixture()
def agent():
    return _client("agent", "binder-agent")


def _active_arena(db, iid, outputs=None):
    db.create_deployment(iid, iid, "custom", provider=None, actor="test")
    db.update_deployment(iid, status="deploying", actor="test")
    db.update_deployment(
        iid, status="active",
        outputs=outputs or {"node_victim_name": "nv-victim"}, actor="test",
    )
    return iid


# --- exec: the core key↔arena gate ------------------------------------------


def test_unbound_agent_cannot_exec(operator, agent):
    _active_arena(operator.db, "bind-exec-1")
    r = agent.post("/arenas/bind-exec-1/exec", json={"node": "victim", "command": "id"})
    assert r.status_code == 403
    assert "not bound" in r.text


def test_operator_bypasses_binding(operator):
    _active_arena(operator.db, "bind-exec-op")
    r = operator.post("/arenas/bind-exec-op/exec", json={"node": "victim", "command": "id"})
    assert r.status_code == 200, r.text


def test_operator_grant_lets_agent_exec(operator, agent):
    _active_arena(operator.db, "bind-exec-2")
    g = operator.post("/arenas/bind-exec-2/bindings", json={"agent_name": "binder-agent"})
    assert g.status_code == 200 and g.json()["bound"] is True
    r = agent.post("/arenas/bind-exec-2/exec", json={"node": "victim", "command": "id"})
    assert r.status_code == 200, r.text


def test_binding_is_per_arena(operator, agent):
    _active_arena(operator.db, "bind-A")
    _active_arena(operator.db, "bind-B")
    operator.post("/arenas/bind-A/bindings", json={"agent_name": "binder-agent"})
    # bound to A only
    assert agent.post("/arenas/bind-A/exec", json={"node": "victim", "command": "id"}).status_code == 200
    assert agent.post("/arenas/bind-B/exec", json={"node": "victim", "command": "id"}).status_code == 403


def test_attacker_file_transfer_is_foothold_scoped_and_hashed(operator, agent):
    outputs = {
        "node_jump_name": "nv-jump",
        "node_jump_ssh_command": "docker exec nv-jump sh",
        "node_victim_name": "nv-victim",
    }
    _active_arena(operator.db, "bind-transfer", outputs)
    operator.post(
        "/arenas/bind-transfer/bindings",
        json={"agent_name": "binder-agent", "stance": "attacker"},
    )
    content = b"payload-proof"
    uploaded = agent.post(
        "/arenas/bind-transfer/files/upload",
        json={"path": "payloads/poc.bin", "content_b64": base64.b64encode(content).decode()},
    )
    assert uploaded.status_code == 200, uploaded.text
    assert uploaded.json()["node"] == "jump"
    assert uploaded.json()["digest"].startswith("sha256:")

    downloaded = agent.post(
        "/arenas/bind-transfer/files/download",
        json={"path": "payloads/poc.bin", "max_bytes": 5},
    )
    assert downloaded.status_code == 200, downloaded.text
    assert base64.b64decode(downloaded.json()["content_b64"]) == content[:5]
    assert downloaded.json()["next_offset"] == 5
    assert downloaded.json()["digest"] == uploaded.json()["digest"]

    assert agent.post(
        "/arenas/bind-transfer/files/upload",
        json={"path": "../escape", "content_b64": "eA=="},
    ).status_code == 422
    assert agent.post(
        "/arenas/bind-transfer/files/download",
        json={"path": "payloads/poc.bin", "node": "victim"},
    ).status_code == 403


def test_headless_browser_is_arena_target_scoped_and_body_free_in_audit(
    operator, agent, monkeypatch
):
    import api

    outputs = {
        "node_jump_name": "nv-jump",
        "node_jump_private_ip": "172.30.0.3",
        "node_jump_ssh_command": "docker exec nv-jump sh",
        "node_victim_name": "nv-victim",
        "node_victim_private_ip": "172.30.0.2",
        "node_victim_ports": {"80": "49000"},
    }
    _active_arena(operator.db, "bind-browser", outputs)
    operator.post(
        "/arenas/bind-browser/bindings",
        json={"agent_name": "binder-agent", "stance": "attacker"},
    )
    seen = {}

    def fake_browser(
        _self, arena, node, ip, port, scheme, path, params, **options
    ):
        seen.update(
            arena=arena, node=node, ip=ip, port=port, scheme=scheme,
            path=path, params=params, options=options,
        )
        return {
            "success": True, "url": "http://172.30.0.2/search?q=secret",
            "title": "Victim", "rendered_dom": "<html>secret body</html>",
            "dom_bytes": 24, "dom_sha256": "sha256:" + "c" * 64,
            "truncated": False, "executed": None,
        }

    monkeypatch.setattr(api.Orchestrator, "browser_visit", fake_browser)
    response = agent.post(
        "/arenas/bind-browser/browser/visit",
        json={"node": "victim", "path": "/search", "params": {"q": "secret"}},
    )
    assert response.status_code == 200, response.text
    assert response.json()["title"] == "Victim"
    assert seen["ip"] == "172.30.0.2" and seen["port"] == 80
    assert seen["scheme"] == "http" and seen["path"] == "/search"

    event = operator.db.list_events("bind-browser", types=("browser_visit",))[0]
    assert event["payload"]["param_names"] == ["q"]
    assert "secret body" not in str(event["payload"])
    assert agent.post(
        "/arenas/bind-browser/browser/visit",
        json={"node": "jump", "path": "/"},
    ).status_code == 403
    assert agent.post(
        "/arenas/bind-browser/browser/visit",
        json={"node": "victim", "path": "http://example.com/"},
    ).status_code == 422


def test_reported_xss_is_confirmed_only_by_browser_execution(operator, agent, monkeypatch):
    import api

    outputs = {
        "node_jump_name": "nv-jump",
        "node_jump_private_ip": "172.31.0.3",
        "node_jump_ssh_command": "docker exec nv-jump sh",
        "node_victim_name": "nv-victim",
        "node_victim_private_ip": "172.31.0.2",
        "node_victim_ports": {"80": "49001"},
    }
    _active_arena(operator.db, "bind-xss-browser", outputs)
    operator.post(
        "/arenas/bind-xss-browser/bindings",
        json={"agent_name": "binder-agent", "stance": "attacker"},
    )
    probes = []

    def fake_browser(
        _self, arena, node, ip, port, scheme, path, params, **options
    ):
        probes.append({"params": params, **options})
        return {
            "success": True, "rendered_dom": "<html></html>", "dom_bytes": 13,
            "dom_sha256": "sha256:" + "d" * 64,
            "executed": bool(options.get("execution_marker")),
        }

    monkeypatch.setattr(api.Orchestrator, "browser_visit", fake_browser)
    finding = agent.post(
        "/arenas/bind-xss-browser/findings",
        json={
            "title": "reflected XSS", "cwe": "CWE-79", "node": "victim",
            "path": "/search", "param": "q", "payload": "agent payload",
        },
    )
    assert finding.status_code == 200, finding.text
    event = operator.db.list_events("bind-xss-browser", types=("finding",))[0]
    assert event["payload"]["validation"]["confirmed"] is True
    assert event["payload"]["validation"]["method"] == "reflected_xss"
    assert probes[0]["execution_marker"].startswith("nv")
    assert "data-nidavellir-xss" in probes[0]["params"]["q"]
    assert "agent payload" not in probes[0]["params"]["q"]


def test_attacker_workspace_is_whitebox_only(operator, agent, monkeypatch):
    import api

    outputs = {
        "node_jump_name": "nv-jump",
        "node_jump_ssh_command": "docker exec nv-jump sh",
        "node_victim_name": "nv-victim",
        "node_victim_sut_source": "/opt/sut",
        "node_victim_whitebox_source": "/whitebox/victim",
        "node_victim_whitebox": True,
    }
    _active_arena(operator.db, "bind-workspace", outputs)
    operator.post(
        "/arenas/bind-workspace/bindings",
        json={"agent_name": "binder-agent", "stance": "attacker"},
    )
    seen = {}

    def fake_diff(_self, arena, node, source_path, **options):
        seen.update(arena=arena, node=node, source_path=source_path, options=options)
        return {
            "success": True, "changed_files": [], "changed_file_count": 0,
            "diff": "", "returned_lines": 0, "total_lines": 0,
            "start_line": 0, "next_start_line": None,
        }

    monkeypatch.setattr(api.Orchestrator, "workspace_diff", fake_diff)
    listing = agent.get("/arenas/bind-workspace/workspaces")
    assert listing.status_code == 200
    workspace = listing.json()["workspaces"][0]
    assert workspace["access"] == "whitebox" and workspace["kind"] == "whitebox"
    assert workspace["writable"] is True

    diff = agent.get("/arenas/bind-workspace/workspaces/victim/diff")
    assert diff.status_code == 200, diff.text
    assert seen["node"] == "jump"
    assert seen["source_path"] == "/whitebox/victim"


def test_workspace_patch_artifact_attaches_to_finding(operator, agent, monkeypatch):
    import api
    outputs = {
        "node_jump_name": "nv-jump",
        "node_jump_ssh_command": "docker exec nv-jump sh",
        "node_victim_name": "nv-victim",
        "node_victim_whitebox_source": "/whitebox/victim",
        "node_victim_whitebox": True,
    }
    _active_arena(operator.db, "bind-evidence", outputs)
    operator.post(
        "/arenas/bind-evidence/bindings",
        json={"agent_name": "binder-agent", "stance": "attacker"},
    )

    def fake_diff(_self, _arena, _node, _source_path, **options):
        lines = ["diff --git a/app.py b/app.py", "-old", "+new"]
        start = options["start_line"]
        page = lines[start:start + 2]
        end = start + len(page)
        return {
            "success": True,
            "baseline": "a" * 40,
            "changed_files": [{"path": "app.py", "index": " ", "worktree": "M"}],
            "changed_file_count": 1,
            "groups": {"staged": [], "unstaged": [{"path": "app.py"}], "untracked": []},
            "diff": "\n".join(page),
            "returned_lines": len(page),
            "total_lines": len(lines),
            "start_line": start,
            "next_start_line": end if end < len(lines) else None,
        }

    monkeypatch.setattr(api.Orchestrator, "workspace_diff", fake_diff)
    exported = agent.post(
        "/arenas/bind-evidence/workspaces/victim/patch-artifacts",
        json={"base": "HEAD"},
    )
    assert exported.status_code == 200, exported.text
    body = exported.json()
    digest = body["artifact"]["digest"]
    assert body["patch"] == "diff --git a/app.py b/app.py\n-old\n+new\n"

    download = agent.get(f"/arenas/bind-evidence/evidence-artifacts/{digest}")
    assert download.status_code == 200 and download.content == body["patch"].encode()

    finding = agent.post(
        "/arenas/bind-evidence/findings",
        json={"title": "changed auth", "evidence_artifact_digests": [digest]},
    )
    assert finding.status_code == 200, finding.text
    event = operator.db.list_events("bind-evidence", types=("finding",), limit=1)[0]
    assert event["payload"]["evidence_artifacts"][0]["digest"] == digest


def test_workspace_patch_rejects_unselected_blackbox(operator, agent):
    _active_arena(
        operator.db,
        "bind-evidence-blackbox",
        {"node_victim_name": "nv-victim", "node_victim_sut_source": "/opt/sut"},
    )
    operator.post(
        "/arenas/bind-evidence-blackbox/bindings",
        json={"agent_name": "binder-agent", "stance": "attacker"},
    )
    response = agent.post(
        "/arenas/bind-evidence-blackbox/workspaces/victim/patch-artifacts",
        json={"base": "HEAD"},
    )
    assert response.status_code == 404


def test_attacker_cannot_enumerate_blackbox_checkout(operator, agent):
    outputs = {
        "node_jump_name": "nv-jump",
        "node_jump_ssh_command": "docker exec nv-jump sh",
        "node_victim_name": "nv-victim",
        "node_victim_sut_source": "/opt/sut",
    }
    _active_arena(operator.db, "bind-blackbox", outputs)
    operator.post(
        "/arenas/bind-blackbox/bindings",
        json={"agent_name": "binder-agent", "stance": "attacker"},
    )
    listing = agent.get("/arenas/bind-blackbox/workspaces")
    assert listing.status_code == 200 and listing.json()["workspaces"] == []
    assert agent.get(
        "/arenas/bind-blackbox/workspaces/victim/diff"
    ).status_code == 404


def test_revoke_blocks_the_agent(operator, agent):
    _active_arena(operator.db, "bind-revoke")
    operator.post("/arenas/bind-revoke/bindings", json={"agent_name": "binder-agent"})
    assert agent.post("/arenas/bind-revoke/exec", json={"node": "victim", "command": "id"}).status_code == 200
    rev = operator.delete("/arenas/bind-revoke/bindings/binder-agent")
    assert rev.status_code == 200 and rev.json()["revoked"] is True
    assert agent.post("/arenas/bind-revoke/exec", json={"node": "victim", "command": "id"}).status_code == 403


# --- pause / resume kill-switch (P2-11) --------------------------------------


def test_pause_blocks_exec_then_resume_restores(operator, agent):
    _active_arena(operator.db, "bind-pause-1")
    operator.post("/arenas/bind-pause-1/bindings", json={"agent_name": "binder-agent"})
    assert agent.post("/arenas/bind-pause-1/exec", json={"node": "victim", "command": "id"}).status_code == 200
    # pause → the binding still exists but gated actions return 423 Locked
    p = operator.post("/arenas/bind-pause-1/bindings/binder-agent/pause")
    assert p.status_code == 200 and p.json()["paused"] is True
    r = agent.post("/arenas/bind-pause-1/exec", json={"node": "victim", "command": "id"})
    assert r.status_code == 423 and "paused" in r.text
    # resume → the agent may drive the arena again
    res = operator.post("/arenas/bind-pause-1/bindings/binder-agent/resume")
    assert res.status_code == 200 and res.json()["paused"] is False
    assert agent.post("/arenas/bind-pause-1/exec", json={"node": "victim", "command": "id"}).status_code == 200


def test_pause_surfaced_in_binding_list(operator, agent):
    _active_arena(operator.db, "bind-pause-list")
    operator.post("/arenas/bind-pause-list/bindings", json={"agent_name": "binder-agent"})
    operator.post("/arenas/bind-pause-list/bindings/binder-agent/pause")
    listing = operator.get("/arenas/bind-pause-list/bindings").json()["bindings"]
    assert len(listing) == 1 and listing[0]["paused"] is True
    operator.post("/arenas/bind-pause-list/bindings/binder-agent/resume")
    listing = operator.get("/arenas/bind-pause-list/bindings").json()["bindings"]
    assert listing[0]["paused"] is False


def test_pause_findings_also_locked(operator, agent):
    _active_arena(operator.db, "bind-pause-find")
    operator.post("/arenas/bind-pause-find/bindings", json={"agent_name": "binder-agent"})
    operator.post("/arenas/bind-pause-find/bindings/binder-agent/pause")
    r = agent.post("/arenas/bind-pause-find/findings",
                   json={"title": "x", "cwe": "CWE-89", "node": "victim"})
    assert r.status_code == 423


def test_pause_is_idempotent_and_resume_noop(operator, agent):
    _active_arena(operator.db, "bind-pause-idem")
    operator.post("/arenas/bind-pause-idem/bindings", json={"agent_name": "binder-agent"})
    assert operator.post("/arenas/bind-pause-idem/bindings/binder-agent/pause").json()["paused"] is True
    # second pause is a no-op (still paused), and reports already-paused
    p2 = operator.post("/arenas/bind-pause-idem/bindings/binder-agent/pause")
    assert p2.status_code == 200 and p2.json()["paused"] is True
    # resume an already-resumed (never-paused) is a no-op
    operator.post("/arenas/bind-pause-idem/bindings/binder-agent/resume")
    r2 = operator.post("/arenas/bind-pause-idem/bindings/binder-agent/resume")
    assert r2.status_code == 200 and r2.json()["paused"] is False


def test_pause_unknown_binding_404(operator):
    _active_arena(operator.db, "bind-pause-404")
    assert operator.post("/arenas/bind-pause-404/bindings/ghost/pause").status_code == 404
    assert operator.post("/arenas/bind-pause-404/bindings/ghost/resume").status_code == 404


def test_pause_endpoints_are_operator_only(operator, agent):
    _active_arena(operator.db, "bind-pause-authz")
    operator.post("/arenas/bind-pause-authz/bindings", json={"agent_name": "binder-agent"})
    assert agent.post("/arenas/bind-pause-authz/bindings/binder-agent/pause").status_code == 403
    assert agent.post("/arenas/bind-pause-authz/bindings/binder-agent/resume").status_code == 403


def test_revoke_then_pause_is_404(operator, agent):
    # A killed (revoked) binding can't be paused — it no longer exists.
    _active_arena(operator.db, "bind-revoke-pause")
    operator.post("/arenas/bind-revoke-pause/bindings", json={"agent_name": "binder-agent"})
    operator.delete("/arenas/bind-revoke-pause/bindings/binder-agent")
    assert operator.post("/arenas/bind-revoke-pause/bindings/binder-agent/pause").status_code == 404


def test_is_paused_unit_ordering():
    # Pure derivation: a fresh grant (or revoke) after a pause clears the paused
    # state; events are newest-first, mirroring db.list_events.
    import bindings as B

    def ev(t):
        return {"type": t, "payload": {"agent_name": "a"}}

    # newest-first: pause is newest → paused
    assert B.is_paused([ev(B.BINDING_PAUSE), ev(B.BINDING_GRANT)], "a") is True
    # resume after pause → not paused
    assert B.is_paused([ev(B.BINDING_RESUME), ev(B.BINDING_PAUSE), ev(B.BINDING_GRANT)], "a") is False
    # a re-grant newer than the pause clears it (active + unpaused)
    assert B.is_paused([ev(B.BINDING_GRANT), ev(B.BINDING_PAUSE), ev(B.BINDING_GRANT)], "a") is False
    # other agents' pause events don't leak
    assert B.is_paused([{"type": B.BINDING_PAUSE, "payload": {"agent_name": "b"}}], "a") is False


# --- stance node-scope (server-side, was gateway-only) -----------------------


def test_attacker_binding_is_foothold_scoped(operator, agent):
    # kali has a shell command → it's the foothold; victim is a target.
    _active_arena(operator.db, "bind-foothold", outputs={
        "node_victim_name": "nv-victim",
        "node_kali_name": "nv-kali",
        "node_kali_ssh_command": "docker exec -it nv-kali bash",
    })
    operator.post("/arenas/bind-foothold/bindings",
                  json={"agent_name": "binder-agent", "stance": "attacker"})
    # exec on the foothold is allowed
    assert agent.post("/arenas/bind-foothold/exec",
                      json={"node": "kali", "command": "id"}).status_code == 200
    # exec directly on the victim (not a foothold) is refused server-side
    r = agent.post("/arenas/bind-foothold/exec", json={"node": "victim", "command": "id"})
    assert r.status_code == 403 and "foothold" in r.text


def test_unrestricted_binding_can_exec_any_node(operator, agent):
    # A stance=None (own-sandbox) binding is NOT foothold-scoped.
    _active_arena(operator.db, "bind-anynode", outputs={
        "node_victim_name": "nv-victim",
        "node_kali_name": "nv-kali",
        "node_kali_ssh_command": "docker exec -it nv-kali bash",
    })
    operator.post("/arenas/bind-anynode/bindings", json={"agent_name": "binder-agent"})
    assert agent.post("/arenas/bind-anynode/exec",
                      json={"node": "victim", "command": "id"}).status_code == 200


# --- self-deploy auto-bind ---------------------------------------------------


def test_agent_self_deploy_autobinds(agent, monkeypatch):
    # The agent deploys a named scenario under its own key → it is auto-bound to
    # the new arena (claimed at deploy). The Celery dispatch is stubbed (no broker
    # in tests); we assert the binding event rather than driving exec.
    import api
    import bindings

    monkeypatch.setattr(api.deploy_lab, "delay", lambda **kw: None)
    r = agent.post("/deploy", json={"scenario": "container_web_pentest", "instance_id": "selfdep"})
    assert r.status_code == 200, r.text
    iid = r.json()["instance_id"]
    events = agent.db.list_events(iid, types=bindings.BINDING_EVENT_TYPES)
    b = bindings.binding_for(events, "binder-agent")
    assert b is not None and b["stance"] is None and b["auto"] is True


# --- findings ----------------------------------------------------------------


def test_findings_require_binding(operator, agent):
    _active_arena(operator.db, "bind-find")
    assert agent.post("/arenas/bind-find/findings",
                      json={"title": "x", "cwe": "CWE-89", "node": "victim"}).status_code == 403
    operator.post("/arenas/bind-find/bindings", json={"agent_name": "binder-agent"})
    assert agent.post("/arenas/bind-find/findings",
                      json={"title": "x", "cwe": "CWE-89", "node": "victim"}).status_code == 200


# --- lifecycle + destructive record operations ------------------------------


def test_agent_can_destroy_only_a_bound_arena(operator, agent, monkeypatch):
    import api

    monkeypatch.setattr(api.destroy_lab, "delay", lambda *args, **kwargs: None)
    _active_arena(operator.db, "bind-destroy-own")
    _active_arena(operator.db, "bind-destroy-other")
    operator.post(
        "/arenas/bind-destroy-own/bindings",
        json={"agent_name": "binder-agent", "stance": "defender"},
    )

    assert agent.delete("/destroy/bind-destroy-other").status_code == 403
    allowed = agent.delete("/destroy/bind-destroy-own")
    assert allowed.status_code == 200
    assert operator.db.get_deployment("bind-destroy-own")["status"] == "destroying"


def test_agent_cannot_delete_or_purge_deployment_records(operator, agent):
    _active_arena(operator.db, "bind-delete-record")
    operator.db.update_deployment("bind-delete-record", status="destroying", actor="test")
    operator.db.update_deployment("bind-delete-record", status="destroyed", actor="test")

    assert agent.delete("/deployments/bind-delete-record").status_code == 403
    assert agent.delete("/deployments").status_code == 403
    assert operator.db.get_deployment("bind-delete-record") is not None


# --- configurator: claimed at setup/start, revoked at finish -----------------


def _sut_like_arena(db, iid):
    return _active_arena(db, iid, outputs={
        "node_victim_name": "nv-victim",
        "node_kali_name": "nv-kali",
        "node_kali_ssh_command": "docker exec -it nv-kali bash",
    })


def test_unbound_agent_cannot_propose_setup(operator, agent):
    _sut_like_arena(operator.db, "bind-cfg-unbound")
    operator.post("/arenas/bind-cfg-unbound/setup/start", json={"mode": "hitl"})  # no agent_name
    r = agent.post("/arenas/bind-cfg-unbound/setup/propose",
                   json={"node": "victim", "command": "echo hi"})
    assert r.status_code == 403 and "not bound" in r.text


def test_setup_start_agent_name_grants_then_finish_revokes(operator, agent):
    _sut_like_arena(operator.db, "bind-cfg-grant")
    s = operator.post("/arenas/bind-cfg-grant/setup/start",
                      json={"mode": "hitl", "agent_name": "binder-agent"})
    assert s.status_code == 200
    # the named agent can now drive the configurator
    assert agent.get("/arenas/bind-cfg-grant/setup/brief").status_code == 200
    # finishing the session revokes the configurator capability
    assert operator.post("/arenas/bind-cfg-grant/setup/finish").json()["finished"] is True
    assert agent.get("/arenas/bind-cfg-grant/setup/brief").status_code == 403


def test_attacker_binding_cannot_drive_setup(operator, agent):
    # Stance enforcement: an attacker-bound agent may exec but not configure.
    _sut_like_arena(operator.db, "bind-cfg-wrongstance")
    operator.post("/arenas/bind-cfg-wrongstance/bindings",
                  json={"agent_name": "binder-agent", "stance": "attacker"})
    operator.post("/arenas/bind-cfg-wrongstance/setup/start", json={"mode": "hitl"})
    r = agent.post("/arenas/bind-cfg-wrongstance/setup/propose",
                   json={"node": "victim", "command": "echo hi"})
    assert r.status_code == 403 and "may not" in r.text


# --- binding management is operator-only -------------------------------------


def test_binding_endpoints_are_operator_only(operator, agent):
    _active_arena(operator.db, "bind-authz")
    assert agent.post("/arenas/bind-authz/bindings", json={"agent_name": "x"}).status_code == 403
    assert agent.get("/arenas/bind-authz/bindings").status_code == 403
    assert agent.delete("/arenas/bind-authz/bindings/x").status_code == 403
    # operator sees the (empty) list
    assert operator.get("/arenas/bind-authz/bindings").json()["bindings"] == []


def test_grant_unknown_stance_rejected(operator):
    _active_arena(operator.db, "bind-badstance")
    r = operator.post("/arenas/bind-badstance/bindings",
                      json={"agent_name": "x", "stance": "wizard"})
    assert r.status_code == 422


def test_bindings_listed_for_operator(operator, agent):
    _active_arena(operator.db, "bind-list")
    operator.post("/arenas/bind-list/bindings", json={"agent_name": "binder-agent", "stance": "attacker"})
    listing = operator.get("/arenas/bind-list/bindings").json()["bindings"]
    assert len(listing) == 1
    assert listing[0]["agent_name"] == "binder-agent" and listing[0]["stance"] == "attacker"
