import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import OutcomeSku, Skill, TaskType, Tool
from app.models.identity import DEMO_CLIENT_ID, DEMO_WORKER_ID, User, WorkerProfileRecord

# Stable UUIDs so re-seeding is idempotent across environments.
SKU_IDS = {
    "launch_studio": uuid.UUID("00000000-0000-4000-8000-000000000001"),
    "brand_starter": uuid.UUID("00000000-0000-4000-8000-000000000002"),
    "landing_launch": uuid.UUID("00000000-0000-4000-8000-000000000003"),
}

SKILLS = [
    ("logo-design", "Logo Design", "design"),
    ("brand-identity", "Brand Identity", "design"),
    ("figma", "Figma", "design"),
    ("react", "React", "frontend"),
    ("tailwind", "Tailwind CSS", "frontend"),
    ("python", "Python", "backend"),
]

TOOLS = [
    ("figma", "Figma", "design"),
    ("illustrator", "Illustrator", "design"),
    ("nextjs", "Next.js", "frontend"),
    ("vercel", "Vercel", "devops"),
]

TASK_TYPES = [
    ("brand_identity", "Brand Identity", "design", 4),
    ("logo_design", "Logo Design", "design", 6),
    ("figma_ui_design", "Figma UI Design", "design", 8),
    ("landing_page_frontend", "Landing Page Frontend", "tech", 10),
    ("deployment_devops", "Deployment / DevOps", "tech", 2),
]

SKUS = [
    {
        "slug": "launch_studio",
        "name": "Launch Studio",
        "category": "combined",
        "description": "Launch-ready brand identity + responsive landing page, designed, built, and deployed.",
        "base_price": Decimal("14000"),
        "typical_days": 10,
    },
    {
        "slug": "brand_starter",
        "name": "Brand Starter",
        "category": "design",
        "description": "Logo, color, type, and a mini brand guide to get you off the ground.",
        "base_price": Decimal("6000"),
        "typical_days": 5,
    },
    {
        "slug": "landing_launch",
        "name": "Landing Launch",
        "category": "tech",
        "description": "A production-ready, responsive landing page deployed to a live URL.",
        "base_price": Decimal("7000"),
        "typical_days": 6,
    },
]


async def seed_catalog(session: AsyncSession) -> None:
    for slug, name, category in SKILLS:
        exists = await session.scalar(select(Skill.id).where(Skill.slug == slug))
        if not exists:
            session.add(Skill(name=name, slug=slug, category=category))

    for slug, name, category in TOOLS:
        exists = await session.scalar(select(Tool.id).where(Tool.slug == slug))
        if not exists:
            session.add(Tool(name=name, slug=slug, category=category))

    for slug, name, community, hours in TASK_TYPES:
        exists = await session.scalar(select(TaskType.id).where(TaskType.slug == slug))
        if not exists:
            session.add(
                TaskType(
                    name=name,
                    slug=slug,
                    community_type=community,
                    typical_hours=Decimal(str(hours)),
                )
            )

    for sku in SKUS:
        exists = await session.scalar(select(OutcomeSku.id).where(OutcomeSku.slug == sku["slug"]))
        if not exists:
            session.add(
                OutcomeSku(
                    id=SKU_IDS[sku["slug"]],
                    slug=sku["slug"],
                    name=sku["name"],
                    category=sku["category"],
                    description=sku["description"],
                    base_price=sku["base_price"],
                    typical_days=sku["typical_days"],
                    revision_limit=2,
                    template_spec={},
                    is_active=True,
                )
            )

    await session.commit()


async def seed_demo_client(session: AsyncSession) -> None:
    exists = await session.get(User, DEMO_CLIENT_ID)
    if exists is None:
        session.add(
            User(
                id=DEMO_CLIENT_ID,
                email="ananya@healthtrack.in",
                full_name="Ananya Sharma",
                role="client",
                is_active=True,
                email_verified=True,
            )
        )
        await session.commit()


async def seed_demo_worker(session: AsyncSession) -> None:
    """Rohan Verma — demo worker for Stage 3 inbox (matches lib/mock-data mockWorkerMe)."""
    user = await session.get(User, DEMO_WORKER_ID)
    if user is None:
        session.add(
            User(
                id=DEMO_WORKER_ID,
                email="rohan@iitd.ac.in",
                full_name="Rohan Verma",
                role="worker",
                is_active=True,
                email_verified=True,
            )
        )
        await session.flush()

    profile = await session.get(WorkerProfileRecord, DEMO_WORKER_ID)
    if profile is None:
        session.add(
            WorkerProfileRecord(
                user_id=DEMO_WORKER_ID,
                community_type="design",
                headline="Brand & logo designer — clean, systematic identities",
                bio=(
                    "IIT Delhi design community. I build brand systems and logos "
                    "with a focus on clarity and reuse. 30+ campus projects delivered."
                ),
                availability_status="available",
                weekly_hours_available=18,
                max_concurrent_tasks=2,
                payout_min=1500,
                payout_max=6000,
                campus_verified=True,
                is_active=True,
                profile_completion_pct=85,
                figma_url="https://figma.com/@rohanverma",
                behance_url="https://behance.net/rohanverma",
                linkedin_url="https://linkedin.com/in/rohanverma",
                skills=[
                    {
                        "skill_id": "skill_logo",
                        "name": "Logo Design",
                        "proficiency": "expert",
                        "years_experience": 3,
                    },
                    {
                        "skill_id": "skill_brand",
                        "name": "Brand Identity",
                        "proficiency": "advanced",
                        "years_experience": 2,
                    },
                    {"skill_id": "skill_figma", "name": "Figma", "proficiency": "advanced"},
                ],
                tools=[
                    {"tool_id": "tool_figma", "name": "Figma", "proficiency": "expert"},
                    {"tool_id": "tool_illustrator", "name": "Illustrator", "proficiency": "advanced"},
                ],
                task_types=[
                    {
                        "task_type_id": "tt_brand",
                        "name": "Brand Identity",
                        "slug": "brand_identity",
                        "proficiency": "advanced",
                    },
                    {
                        "task_type_id": "tt_logo",
                        "name": "Logo Design",
                        "slug": "logo_design",
                        "proficiency": "expert",
                    },
                ],
                portfolio=[
                    {
                        "id": "pf_1",
                        "worker_id": str(DEMO_WORKER_ID),
                        "title": "Medlink — clinic brand identity",
                        "description": "Full brand system for a telehealth clinic.",
                        "category": "Brand Identity",
                        "cover_image_url": None,
                        "project_url": "https://behance.net/rohanverma/medlink",
                        "tags": ["healthcare", "branding", "logo"],
                        "tools_used": ["Figma", "Illustrator"],
                        "is_featured": True,
                    }
                ],
                stats={
                    "worker_id": str(DEMO_WORKER_ID),
                    "tasks_completed": 27,
                    "on_time_pct": 96,
                    "avg_qa_score": 91,
                    "avg_rating": 4.8,
                    "response_time_hours": 3.2,
                    "seller_level": "trusted",
                    "last_active_at": None,
                },
            )
        )
        await session.commit()
