import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import OutcomeSku, Skill, TaskType, Tool
from app.models.identity import DEMO_CLIENT_ID, User

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
