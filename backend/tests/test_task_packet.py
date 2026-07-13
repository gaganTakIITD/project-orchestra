"""Task Packet Generator — fixture + gateway proposal paths."""

from app.ai.gateway import generate_task_packet_proposal
from app.ai.task_packet_generator import generate_charter_and_packet
from app.config import settings


class _FakeTask:
    def __init__(self):
        import uuid

        self.id = uuid.uuid4()
        self.title = "Logo design"
        self.description = "Design the logo in SVG + PNG."
        self.task_type_slug = "logo_design"
        self.acceptance_criteria = [
            {
                "criterion": "Logo delivered in SVG and PNG",
                "check_type": "deterministic",
                "rule": "files_include_format(['svg','png'])",
            }
        ]
        self.deadline = None
        self.depends_on = []


def test_generate_charter_and_packet_slices_logo():
    import uuid

    task = _FakeTask()
    charter, packet = generate_charter_and_packet(
        order_id=uuid.uuid4(),
        task=task,
        spec={
            "outcome_statement": "Launch-ready brand and landing for HealthTrack.",
            "deliverables": [
                {"name": "Logo", "format": "SVG + PNG", "required": True},
                {"name": "Brand guide", "format": "PDF", "required": True},
            ],
            "out_of_scope": ["CMS"],
            "client_inputs_required": ["company_name", "tagline"],
        },
        order_price_share=2000,
        order_deadline=None,
        revision_limit=2,
        dependency_titles=["Brand direction"],
    )
    assert charter["task_id"] == task.id
    assert charter["snapshot"]["deliverables"]
    assert any("Logo" in d["name"] for d in charter["snapshot"]["deliverables"])
    assert packet["charter_id"] == charter["id"]
    assert len(packet["checklist"]) >= 1
    assert packet["dependencies"] == ["Brand direction"]
    assert "tagline" in packet["client_inputs"]


def test_gateway_task_packet_proposal_matches_fixture(monkeypatch):
    import uuid

    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "require_gemini", False)
    monkeypatch.setattr(settings, "app_env", "development")

    task = _FakeTask()
    proposal = generate_task_packet_proposal(
        order_id=uuid.uuid4(),
        task=task,
        spec={
            "outcome_statement": "Launch-ready brand and landing for HealthTrack.",
            "deliverables": [
                {"name": "Logo", "format": "SVG + PNG", "required": True},
                {"name": "Brand guide", "format": "PDF", "required": True},
            ],
            "out_of_scope": ["CMS"],
            "client_inputs_required": ["company_name", "tagline"],
        },
        order_price_share=2000,
        order_deadline=None,
        revision_limit=2,
        dependency_titles=["Brand direction"],
    )
    assert proposal.source == "fixture"
    assert proposal.error is None
    assert any("Logo" in d["name"] for d in proposal.charter["snapshot"]["deliverables"])
    assert proposal.packet["dependencies"] == ["Brand direction"]
