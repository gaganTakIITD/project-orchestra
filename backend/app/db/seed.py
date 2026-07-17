import uuid
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import OutcomeSku, Skill, TaskType, Tool
from app.models.identity import (
    DEMO_CLIENT_ID,
    DEMO_WORKER_AISHA_ID,
    DEMO_WORKER_DEV_ID,
    DEMO_WORKER_FAKE_LEX_ID,
    DEMO_WORKER_FAKE_RIA_ID,
    DEMO_WORKER_FAKE_SAM_ID,
    DEMO_WORKER_ID,
    DEMO_WORKER_JAYA_ID,
    DEMO_WORKER_KABIR_ID,
    DEMO_WORKER_MEERA_ID,
    DEMO_WORKER_NEEL_ID,
    SEED_WORKER_POOL_IDS,
    User,
    WorkerProfileRecord,
)

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


async def purge_seed_workers(session: AsyncSession) -> None:
    """Deactivate all seeded workers so they leave the live matcher pool.

    Safety: only touch seed-pool UUIDs with no Clerk link (`external_auth_id IS NULL`).
    Never deactivates a real registered account that collided onto a seed email/id.
    """
    for user_id in SEED_WORKER_POOL_IDS:
        user = await session.get(User, user_id)
        if user is None:
            continue
        if user.external_auth_id is not None:
            continue
        user.is_active = False
        profile = await session.get(WorkerProfileRecord, user_id)
        if profile is not None:
            profile.is_active = False
    await session.commit()


async def seed_demo_worker_pool(session: AsyncSession) -> None:
    """Create exactly 10 matcher profiles for pytest / local demo auth.

    Originals (campus_verified=True, @iitd.ac.in):
      Rohan, Meera, Kabir, Aisha, Arjun
    Fakes (campus_verified=False, @orchestra.demo):
      Jaya, Neel, Ria, Sam, Lex

    Production boot must call ``purge_seed_workers`` instead — seeds stay out of
    the live matcher pool.
    """
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
                    {
                        "task_type_id": "tt_figma",
                        "name": "Figma UI Design",
                        "slug": "figma_ui_design",
                        "proficiency": "advanced",
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
    else:
        slugs = {t.get("slug") for t in (profile.task_types or [])}
        if "figma_ui_design" not in slugs:
            profile.task_types = list(profile.task_types or []) + [
                {
                    "task_type_id": "tt_figma",
                    "name": "Figma UI Design",
                    "slug": "figma_ui_design",
                    "proficiency": "advanced",
                }
            ]
        profile.is_active = True
        profile.campus_verified = True

    # --- 5 original campus talent ---
    await _ensure_pool_worker(
        session,
        user_id=DEMO_WORKER_MEERA_ID,
        email="meera@iitd.ac.in",
        full_name="Meera Nair",
        headline="Identity designer, motion-curious",
        bio="Minimal brand systems and logo craft for early-stage products.",
        community_type="design",
        availability_status="available",
        proficiency="advanced",
        task_slugs=("brand_identity", "logo_design", "figma_ui_design"),
        tasks_completed=14,
        on_time_pct=94,
        seller_level="rising",
        campus_verified=True,
    )
    await _ensure_pool_worker(
        session,
        user_id=DEMO_WORKER_KABIR_ID,
        email="kabir@iitd.ac.in",
        full_name="Kabir Anand",
        headline="Designer & illustrator",
        bio="Illustration-led identities with a warm, hand-crafted feel.",
        community_type="design",
        availability_status="busy",
        proficiency="intermediate",
        task_slugs=("brand_identity", "logo_design", "figma_ui_design"),
        tasks_completed=9,
        on_time_pct=90,
        seller_level="rising",
        campus_verified=True,
    )
    await _ensure_pool_worker(
        session,
        user_id=DEMO_WORKER_AISHA_ID,
        email="aisha@iitd.ac.in",
        full_name="Aisha Khan",
        headline="Product UI designer — Figma systems",
        bio="Landing and dashboard UI in Figma with strong accessibility habits.",
        community_type="design",
        availability_status="available",
        proficiency="expert",
        task_slugs=("figma_ui_design", "brand_identity", "logo_design"),
        tasks_completed=22,
        on_time_pct=97,
        seller_level="trusted",
        campus_verified=True,
    )
    await _ensure_pool_worker(
        session,
        user_id=DEMO_WORKER_DEV_ID,
        email="arjun@iitd.ac.in",
        full_name="Arjun Patel",
        headline="Frontend engineer — Next.js & Tailwind",
        bio="Ships fast, accessible landing pages with Lighthouse-friendly builds.",
        community_type="tech",
        availability_status="available",
        proficiency="advanced",
        task_slugs=("landing_page_frontend", "deployment_devops"),
        tasks_completed=31,
        on_time_pct=95,
        seller_level="trusted",
        campus_verified=True,
    )

    # --- 5 fake demo fillers (matching padding; not campus-verified) ---
    await _ensure_pool_worker(
        session,
        user_id=DEMO_WORKER_JAYA_ID,
        email="jaya.fake@orchestra.demo",
        full_name="Jaya Reddy",
        headline="[Demo] Full-stack builder & deploy wrangler",
        bio="Fake demo profile for matcher shortlists — production deploys and marketing sites.",
        community_type="tech",
        availability_status="available",
        proficiency="advanced",
        task_slugs=("landing_page_frontend", "deployment_devops", "figma_ui_design"),
        tasks_completed=18,
        on_time_pct=93,
        seller_level="rising",
        campus_verified=False,
    )
    await _ensure_pool_worker(
        session,
        user_id=DEMO_WORKER_NEEL_ID,
        email="neel.fake@orchestra.demo",
        full_name="Neel Sharma",
        headline="[Demo] React engineer — performance & a11y",
        bio="Fake demo profile for matcher shortlists — Vercel landings with strong Lighthouse scores.",
        community_type="tech",
        availability_status="busy",
        proficiency="intermediate",
        task_slugs=("landing_page_frontend", "deployment_devops"),
        tasks_completed=12,
        on_time_pct=91,
        seller_level="rising",
        campus_verified=False,
    )
    await _ensure_pool_worker(
        session,
        user_id=DEMO_WORKER_FAKE_RIA_ID,
        email="ria.fake@orchestra.demo",
        full_name="Ria Kapoor",
        headline="[Demo] Brand systems & wordmarks",
        bio="Fake demo designer — crisp logo systems for campus pilots.",
        community_type="design",
        availability_status="available",
        proficiency="advanced",
        task_slugs=("brand_identity", "logo_design", "figma_ui_design"),
        tasks_completed=11,
        on_time_pct=92,
        seller_level="rising",
        campus_verified=False,
    )
    await _ensure_pool_worker(
        session,
        user_id=DEMO_WORKER_FAKE_SAM_ID,
        email="sam.fake@orchestra.demo",
        full_name="Sam Okonkwo",
        headline="[Demo] Landing page engineer",
        bio="Fake demo tech profile — Next.js landings and light DevOps.",
        community_type="tech",
        availability_status="available",
        proficiency="advanced",
        task_slugs=("landing_page_frontend", "deployment_devops"),
        tasks_completed=16,
        on_time_pct=94,
        seller_level="rising",
        campus_verified=False,
    )
    await _ensure_pool_worker(
        session,
        user_id=DEMO_WORKER_FAKE_LEX_ID,
        email="lex.fake@orchestra.demo",
        full_name="Lex Chen",
        headline="[Demo] UI craft & design systems",
        bio="Fake demo designer — Figma UI kits and brand-adjacent product screens.",
        community_type="design",
        availability_status="available",
        proficiency="intermediate",
        task_slugs=("figma_ui_design", "brand_identity", "logo_design"),
        tasks_completed=8,
        on_time_pct=89,
        seller_level="new",
        campus_verified=False,
    )

    # Keep seed pool at exactly these 10 — deactivate any other seeded demo UUIDs
    # in the 020–02f range that are not in the canonical list (idempotent).
    pool_ids = set(SEED_WORKER_POOL_IDS)
    seeded_range = await session.execute(
        select(User).where(
            User.role == "worker",
            or_(
                User.email.like("%@iitd.ac.in"),
                User.email.like("%@orchestra.demo"),
            ),
        )
    )
    for row in seeded_range.scalars().all():
        if row.id not in pool_ids and str(row.id).startswith("00000000-0000-4000-8000-00000000002"):
            row.is_active = False
            profile = await session.get(WorkerProfileRecord, row.id)
            if profile is not None:
                profile.is_active = False

    await session.commit()


_TASK_TYPE_LABELS = {
    "brand_identity": ("tt_brand", "Brand Identity"),
    "logo_design": ("tt_logo", "Logo Design"),
    "figma_ui_design": ("tt_figma", "Figma UI Design"),
    "landing_page_frontend": ("tt_landing", "Landing Page Frontend"),
    "deployment_devops": ("tt_deploy", "Deployment / DevOps"),
}


async def _ensure_pool_worker(
    session: AsyncSession,
    *,
    user_id,
    email: str,
    full_name: str,
    headline: str,
    bio: str,
    community_type: str,
    availability_status: str,
    proficiency: str,
    task_slugs: tuple[str, ...],
    tasks_completed: int,
    on_time_pct: float,
    seller_level: str,
    campus_verified: bool = True,
) -> None:
    user = await session.get(User, user_id)
    if user is None:
        session.add(
            User(
                id=user_id,
                email=email,
                full_name=full_name,
                role="worker",
                is_active=True,
                email_verified=True,
            )
        )
        await session.flush()
    else:
        user.email = email
        user.full_name = full_name
        user.is_active = True

    profile = await session.get(WorkerProfileRecord, user_id)
    if profile is not None:
        # Refresh task coverage on existing pool workers (idempotent deepen).
        profile.task_types = [
            {
                "task_type_id": _TASK_TYPE_LABELS[slug][0],
                "name": _TASK_TYPE_LABELS[slug][1],
                "slug": slug,
                "proficiency": proficiency,
            }
            for slug in task_slugs
            if slug in _TASK_TYPE_LABELS
        ]
        profile.community_type = community_type
        profile.headline = headline
        profile.bio = bio
        profile.availability_status = availability_status
        profile.campus_verified = campus_verified
        profile.is_active = True
        if (profile.profile_completion_pct or 0) < 70:
            profile.profile_completion_pct = 80
        profile.stats = {
            "worker_id": str(user_id),
            "tasks_completed": tasks_completed,
            "on_time_pct": on_time_pct,
            "avg_qa_score": 88,
            "avg_rating": 4.5,
            "response_time_hours": 4.0,
            "seller_level": seller_level,
            "last_active_at": None,
        }
        return

    session.add(
        WorkerProfileRecord(
            user_id=user_id,
            community_type=community_type,
            headline=headline,
            bio=bio,
            availability_status=availability_status,
            weekly_hours_available=12,
            max_concurrent_tasks=2,
            payout_min=1200,
            payout_max=4500,
            campus_verified=campus_verified,
            is_active=True,
            profile_completion_pct=80,
            skills=[
                {
                    "skill_id": "skill_logo",
                    "name": "Logo Design",
                    "proficiency": proficiency,
                },
                {
                    "skill_id": "skill_brand",
                    "name": "Brand Identity",
                    "proficiency": "intermediate",
                },
            ],
            tools=[
                {"tool_id": "tool_figma", "name": "Figma", "proficiency": "advanced"},
                {"tool_id": "tool_illustrator", "name": "Illustrator", "proficiency": proficiency},
            ],
            task_types=[
                {
                    "task_type_id": _TASK_TYPE_LABELS[slug][0],
                    "name": _TASK_TYPE_LABELS[slug][1],
                    "slug": slug,
                    "proficiency": proficiency,
                }
                for slug in task_slugs
                if slug in _TASK_TYPE_LABELS
            ],
            portfolio=[
                {
                    "id": f"pf_{user_id.hex[:8]}",
                    "worker_id": str(user_id),
                    "title": f"{full_name.split()[0]} sample mark",
                    "description": "Sample identity work",
                    "tags": ["logo", "branding"],
                    "tools_used": ["Figma"],
                    "is_featured": True,
                }
            ],
            stats={
                "worker_id": str(user_id),
                "tasks_completed": tasks_completed,
                "on_time_pct": on_time_pct,
                "avg_qa_score": 88,
                "avg_rating": 4.5,
                "response_time_hours": 4.0,
                "seller_level": seller_level,
                "last_active_at": None,
            },
        )
    )


# Backward-compatible alias — tests historically imported ``seed_demo_worker``.
seed_demo_worker = seed_demo_worker_pool
