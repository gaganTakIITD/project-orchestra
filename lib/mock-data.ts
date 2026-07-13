/**
 * Project Orchestra — Mock Data (contract-aware fixtures)
 * =======================================================
 * A coherent "Launch Studio" scenario (brand + landing page for a healthcare
 * startup), matching the Spec Compiler / Architect examples in Technical Spec
 * §8.2–§8.4. Shaped EXACTLY like the API contract in `lib/types.ts`, so screens
 * built by v0 against this data will work unchanged once the real backend lands.
 *
 * OWNERSHIP: thin-frontend (Cursor) side. Extend here; do not hardcode data in UI.
 */
import type {
  AppNotification,
  Candidate,
  Charter,
  TaskPacket,
  DeliveryBundle,
  DiscussionThread,
  FulfillmentPlan,
  Intent,
  OutcomeOrder,
  OutcomeSku,
  OutcomeSpec,
  PreferenceSet,
  QAReview,
  Quote,
  Skill,
  Submission,
  TaskActivation,
  TaskInterest,
  TaskType,
  Tool,
  User,
  WorkerProfile,
} from "./types";

/** Deterministic-ish relative date helper so deadlines stay in the future. */
const daysFromNow = (n: number): string => {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return d.toISOString();
};
const hoursFromNow = (n: number): string => {
  const d = new Date();
  d.setHours(d.getHours() + n);
  return d.toISOString();
};

// ----------------------------------------------------------------------------
// Users
// ----------------------------------------------------------------------------

export const mockClient: User = {
  id: "usr_client_ananya",
  email: "ananya@healthtrack.in",
  full_name: "Ananya Sharma",
  role: "client",
  profile_photo_url: null,
  is_active: true,
  email_verified: true,
  created_at: daysFromNow(-20),
};

/** The logged-in worker used by the worker dashboard. */
export const mockWorkerMe: WorkerProfile = {
  user_id: "usr_worker_rohan",
  full_name: "Rohan Verma",
  profile_photo_url: null,
  community_type: "design",
  headline: "Brand & logo designer — clean, systematic identities",
  bio: "IIT Delhi design community. I build brand systems and logos with a focus on clarity and reuse. 30+ campus projects delivered.",
  availability_status: "available",
  weekly_hours_available: 18,
  max_concurrent_tasks: 2,
  payout_min: 1500,
  payout_max: 6000,
  campus_verified: true,
  is_active: true,
  profile_completion_pct: 85,
  github_url: null,
  figma_url: "https://figma.com/@rohanverma",
  behance_url: "https://behance.net/rohanverma",
  linkedin_url: "https://linkedin.com/in/rohanverma",
  skills: [
    { skill_id: "skill_logo", name: "Logo Design", proficiency: "expert", years_experience: 3 },
    { skill_id: "skill_brand", name: "Brand Identity", proficiency: "advanced", years_experience: 2 },
    { skill_id: "skill_figma", name: "Figma", proficiency: "advanced" },
  ],
  tools: [
    { tool_id: "tool_figma", name: "Figma", proficiency: "expert" },
    { tool_id: "tool_illustrator", name: "Illustrator", proficiency: "advanced" },
  ],
  task_types: [
    { task_type_id: "tt_brand", name: "Brand Identity", slug: "brand_identity", proficiency: "advanced" },
    { task_type_id: "tt_logo", name: "Logo Design", slug: "logo_design", proficiency: "expert" },
  ],
  portfolio: [
    {
      id: "pf_1",
      worker_id: "usr_worker_rohan",
      title: "Medlink — clinic brand identity",
      description: "Full brand system for a telehealth clinic.",
      category: "Brand Identity",
      cover_image_url: null,
      project_url: "https://behance.net/rohanverma/medlink",
      tags: ["healthcare", "branding", "logo"],
      tools_used: ["Figma", "Illustrator"],
      is_featured: true,
    },
  ],
  stats: {
    worker_id: "usr_worker_rohan",
    tasks_completed: 27,
    on_time_pct: 96,
    avg_qa_score: 91,
    avg_rating: 4.8,
    response_time_hours: 3.2,
    seller_level: "trusted",
    last_active_at: hoursFromNow(-2),
  },
};

// ----------------------------------------------------------------------------
// Taxonomy (Spec §4.2, §4.10 seed)
// ----------------------------------------------------------------------------

export const mockSkills: Skill[] = [
  { id: "skill_logo", name: "Logo Design", slug: "logo-design", category: "design" },
  { id: "skill_brand", name: "Brand Identity", slug: "brand-identity", category: "design" },
  { id: "skill_figma", name: "Figma", slug: "figma", category: "design" },
  { id: "skill_react", name: "React", slug: "react", category: "frontend" },
  { id: "skill_tailwind", name: "Tailwind CSS", slug: "tailwind", category: "frontend" },
  { id: "skill_python", name: "Python", slug: "python", category: "backend" },
];

export const mockTools: Tool[] = [
  { id: "tool_figma", name: "Figma", slug: "figma", category: "design" },
  { id: "tool_illustrator", name: "Illustrator", slug: "illustrator", category: "design" },
  { id: "tool_nextjs", name: "Next.js", slug: "nextjs", category: "frontend" },
  { id: "tool_vercel", name: "Vercel", slug: "vercel", category: "devops" },
];

export const mockTaskTypes: TaskType[] = [
  { id: "tt_brand", name: "Brand Identity", slug: "brand_identity", community_type: "design", typical_hours: 4 },
  { id: "tt_logo", name: "Logo Design", slug: "logo_design", community_type: "design", typical_hours: 6 },
  { id: "tt_figma_ui", name: "Figma UI Design", slug: "figma_ui_design", community_type: "design", typical_hours: 8 },
  { id: "tt_landing", name: "Landing Page Frontend", slug: "landing_page_frontend", community_type: "tech", typical_hours: 10 },
  { id: "tt_deploy", name: "Deployment / DevOps", slug: "deployment_devops", community_type: "tech", typical_hours: 2 },
];

export const mockSkus: OutcomeSku[] = [
  {
    id: "sku_launch_studio",
    slug: "launch_studio",
    name: "Launch Studio",
    category: "combined",
    description: "Launch-ready brand identity + responsive landing page, designed, built, and deployed.",
    base_price: 14000,
    typical_days: 10,
    revision_limit: 2,
  },
  {
    id: "sku_brand_starter",
    slug: "brand_starter",
    name: "Brand Starter",
    category: "design",
    description: "Logo, color, type, and a mini brand guide to get you off the ground.",
    base_price: 6000,
    typical_days: 5,
    revision_limit: 2,
  },
  {
    id: "sku_landing_launch",
    slug: "landing_launch",
    name: "Landing Launch",
    category: "tech",
    description: "A production-ready, responsive landing page deployed to a live URL.",
    base_price: 7000,
    typical_days: 6,
    revision_limit: 2,
  },
];

// ----------------------------------------------------------------------------
// The Launch Studio order (intent -> spec -> quote -> order)
// ----------------------------------------------------------------------------

export const mockIntent: Intent = {
  id: "int_healthtrack",
  client_id: mockClient.id,
  raw_text:
    "I need a brand and a landing page for my healthcare startup, HealthTrack. It helps people track chronic conditions. Should feel trustworthy and modern.",
  attachments: [],
  status: "compiled",
  created_at: daysFromNow(-6),
};

export const mockSpec: OutcomeSpec = {
  id: "spec_healthtrack",
  intent_id: mockIntent.id,
  sku_id: "sku_launch_studio",
  outcome_statement: "Launch-ready HealthTrack brand identity and responsive landing page.",
  deliverables: [
    { name: "Logo", format: "SVG + PNG", required: true },
    { name: "Brand guide", format: "PDF", required: true },
    { name: "Figma UI", format: "Figma link", required: true },
    { name: "Live landing page", format: "URL", required: true },
  ],
  acceptance_criteria: [
    { criterion: "Logo delivered in SVG and PNG", check_type: "deterministic", rule: "files_include_format(['svg','png'])" },
    { criterion: "Landing page loads under 3s on mobile", check_type: "deterministic", rule: "lighthouse_performance >= 70" },
    { criterion: "Visual design matches a trustworthy, modern healthcare tone", check_type: "ai_judged", rubric: "Professional, calm palette; clear hierarchy; accessible contrast." },
    { criterion: "Page is responsive on mobile and desktop", check_type: "deterministic", rule: "responsive_check_pass" },
  ],
  in_scope: ["1 landing page", "2 revision rounds", "Logo + brand guide"],
  out_of_scope: ["CMS", "SEO", "Content writing", "Mobile app"],
  assumptions: ["Client provides company name and tagline"],
  client_inputs_required: ["company_name", "tagline", "reference_sites"],
  mapped_task_types: ["brand_identity", "logo_design", "figma_ui_design", "landing_page_frontend", "deployment_devops"],
  risk_tier: "L1",
  workflow_summary:
    "Brand direction → Logo design → UI design in Figma → Build landing page → Deploy to live URL",
  version: 1,
  frozen_at: daysFromNow(-5),
};

export const mockQuote: Quote = {
  id: "quote_healthtrack",
  spec_id: mockSpec.id,
  client_id: mockClient.id,
  price: 14000,
  deadline: daysFromNow(9),
  revision_limit: 2,
  status: "accepted",
  valid_until: daysFromNow(-3),
  ai_confidence: 0.88,
  ai_rationale: "Standard Launch Studio scope; effort within typical band for 5-task DAG.",
  created_at: daysFromNow(-6),
};

export const mockOrder: OutcomeOrder = {
  id: "ord_healthtrack",
  client_id: mockClient.id,
  quote_id: mockQuote.id,
  spec_id: mockSpec.id,
  sku_id: "sku_launch_studio",
  status: "delivery_active",
  price: 14000,
  deadline: daysFromNow(9),
  revision_limit: 2,
  progress_pct: 40,
  created_at: daysFromNow(-5),
  updated_at: hoursFromNow(-4),
};

/**
 * The demo client's full outcome list — powers the /orders dashboard (useMyOrders).
 * Newest first, mirroring the real `GET /orders` ordering (created_at desc).
 */
export const mockOrders: OutcomeOrder[] = [
  {
    id: "ord_brandkit",
    client_id: mockClient.id,
    quote_id: "quote_brandkit",
    spec_id: mockSpec.id,
    sku_id: "sku_launch_studio",
    status: "assembling_team",
    price: 4500,
    deadline: daysFromNow(14),
    revision_limit: 2,
    progress_pct: 0,
    created_at: hoursFromNow(-6),
    updated_at: hoursFromNow(-6),
  },
  mockOrder,
  {
    id: "ord_pitchdeck",
    client_id: mockClient.id,
    quote_id: "quote_pitchdeck",
    spec_id: mockSpec.id,
    sku_id: "sku_launch_studio",
    status: "delivered",
    price: 6000,
    deadline: daysFromNow(2),
    revision_limit: 2,
    progress_pct: 100,
    created_at: daysFromNow(-12),
    updated_at: hoursFromNow(-20),
  },
];

// ----------------------------------------------------------------------------
// Fulfillment plan — the 5-task DAG (Spec §8.3 Architect example)
// ----------------------------------------------------------------------------

export const mockPlan: FulfillmentPlan = {
  id: "plan_healthtrack",
  order_id: mockOrder.id,
  critical_path_hours: 30,
  milestones: [
    { name: "Brand ready", task_ids: ["task_brand", "task_logo"], client_label: "Brand identity complete" },
    { name: "Design ready", task_ids: ["task_ui"], client_label: "UI design complete" },
    { name: "Live site", task_ids: ["task_landing", "task_deploy"], client_label: "Website live" },
  ],
  tasks: [
    {
      id: "task_brand",
      plan_id: "plan_healthtrack",
      order_id: mockOrder.id,
      task_type_id: "tt_brand",
      task_type_slug: "brand_identity",
      title: "Brand direction",
      description: "Define the visual direction: mood, palette, typography.",
      acceptance_criteria: [
        { criterion: "Mood board + palette + type approved", check_type: "human_required" },
      ],
      status: "completed",
      sequence_order: 1,
      payout_amount: 1500,
      deadline: daysFromNow(-3),
      assigned_worker_id: "usr_worker_meera",
      revision_count: 0,
      revision_limit: 2,
      depends_on: [],
      started_at: daysFromNow(-5),
      completed_at: daysFromNow(-3),
    },
    {
      id: "task_logo",
      plan_id: "plan_healthtrack",
      order_id: mockOrder.id,
      task_type_id: "tt_logo",
      task_type_slug: "logo_design",
      title: "Logo design",
      description: "Design the HealthTrack logo in SVG + PNG.",
      acceptance_criteria: [
        { criterion: "Logo delivered in SVG and PNG", check_type: "deterministic", rule: "files_include_format(['svg','png'])" },
        { criterion: "Matches approved brand direction", check_type: "ai_judged", rubric: "Consistent with mood board and palette." },
      ],
      status: "priority_active",
      sequence_order: 2,
      payout_amount: 2000,
      deadline: daysFromNow(2),
      assigned_worker_id: null,
      revision_count: 0,
      revision_limit: 2,
      priority_window_ends: hoursFromNow(20),
      depends_on: ["task_brand"],
    },
    {
      id: "task_ui",
      plan_id: "plan_healthtrack",
      order_id: mockOrder.id,
      task_type_id: "tt_figma_ui",
      task_type_slug: "figma_ui_design",
      title: "UI design",
      description: "Design the landing page UI in Figma.",
      acceptance_criteria: [
        { criterion: "Desktop + mobile frames", check_type: "human_required" },
      ],
      status: "blocked",
      sequence_order: 3,
      payout_amount: 3000,
      deadline: daysFromNow(5),
      assigned_worker_id: null,
      revision_count: 0,
      revision_limit: 2,
      depends_on: ["task_logo"],
    },
    {
      id: "task_landing",
      plan_id: "plan_healthtrack",
      order_id: mockOrder.id,
      task_type_id: "tt_landing",
      task_type_slug: "landing_page_frontend",
      title: "Build landing page",
      description: "Implement the landing page (Next.js + Tailwind).",
      acceptance_criteria: [
        { criterion: "Lighthouse performance >= 70 on mobile", check_type: "deterministic", rule: "lighthouse_performance >= 70" },
        { criterion: "Responsive on mobile and desktop", check_type: "deterministic", rule: "responsive_check_pass" },
      ],
      status: "blocked",
      sequence_order: 4,
      payout_amount: 4000,
      deadline: daysFromNow(8),
      assigned_worker_id: null,
      revision_count: 0,
      revision_limit: 2,
      depends_on: ["task_ui"],
    },
    {
      id: "task_deploy",
      plan_id: "plan_healthtrack",
      order_id: mockOrder.id,
      task_type_id: "tt_deploy",
      task_type_slug: "deployment_devops",
      title: "Deploy",
      description: "Deploy the landing page to a live URL.",
      acceptance_criteria: [
        { criterion: "URL reachable (200)", check_type: "deterministic", rule: "url_reachable" },
      ],
      status: "blocked",
      sequence_order: 5,
      payout_amount: 1000,
      deadline: daysFromNow(9),
      assigned_worker_id: null,
      revision_count: 0,
      revision_limit: 2,
      depends_on: ["task_landing"],
    },
  ],
};

// ----------------------------------------------------------------------------
// Matching — candidates for the logo task (Spec §8.4)
// ----------------------------------------------------------------------------

export const mockCandidates: Candidate[] = [
  {
    worker_id: "usr_worker_rohan",
    full_name: "Rohan Verma",
    profile_photo_url: null,
    headline: "Brand & logo designer — clean, systematic identities",
    community_type: "design",
    score: 0.92,
    rationale: "Expert in logo_design, 27 completed tasks, 96% on-time, healthcare brand in portfolio.",
    availability: "available",
    seller_level: "trusted",
    tasks_completed: 27,
    on_time_pct: 96,
  },
  {
    worker_id: "usr_worker_meera",
    full_name: "Meera Nair",
    profile_photo_url: null,
    headline: "Identity designer, motion-curious",
    community_type: "design",
    score: 0.86,
    rationale: "Advanced logo_design, strong minimalist portfolio, 94% on-time.",
    availability: "available",
    seller_level: "rising",
    tasks_completed: 14,
    on_time_pct: 94,
  },
  {
    worker_id: "usr_worker_kabir",
    full_name: "Kabir Anand",
    profile_photo_url: null,
    headline: "Designer & illustrator",
    community_type: "design",
    score: 0.79,
    rationale: "Good fit on style; fewer healthcare samples; 90% on-time.",
    availability: "busy",
    seller_level: "rising",
    tasks_completed: 9,
    on_time_pct: 90,
  },
];

export const mockPreferenceSet: PreferenceSet = {
  id: "pref_logo",
  task_id: "task_logo",
  order_id: mockOrder.id,
  entries: [
    { worker_id: "usr_worker_rohan", rank: 1 },
    { worker_id: "usr_worker_meera", rank: 2 },
    { worker_id: "usr_worker_kabir", rank: 3 },
  ],
  created_at: daysFromNow(-3),
};

export const mockInterests: TaskInterest[] = [
  { id: "int_rohan", task_id: "task_logo", worker_id: "usr_worker_rohan", status: "accepted", rank_at_accept: 1, accepted_at: hoursFromNow(-6) },
  { id: "int_meera", task_id: "task_logo", worker_id: "usr_worker_meera", status: "accepted", rank_at_accept: 2, accepted_at: hoursFromNow(-5) },
];

export const mockActivation: TaskActivation = {
  id: "act_rohan",
  task_id: "task_logo",
  worker_id: "usr_worker_rohan",
  activation_type: "priority",
  window_starts: hoursFromNow(-4),
  window_ends: hoursFromNow(20),
  status: "active",
};

// ----------------------------------------------------------------------------
// Delivery & quality — a completed task's submission + QA (Spec §8.5)
// ----------------------------------------------------------------------------

export const mockSubmission: Submission = {
  id: "sub_brand",
  task_id: "task_brand",
  worker_id: "usr_worker_meera",
  notes: "Mood board, palette (calm blues/greens), and type pairing attached.",
  asset_urls: ["https://files.example/brand-direction.pdf"],
  version: 1,
  submitted_at: daysFromNow(-3),
};

export const mockQAReview: QAReview = {
  id: "qa_brand",
  submission_id: "sub_brand",
  task_id: "task_brand",
  result: "pass",
  score: 92,
  confidence: 0.9,
  feedback: "Direction is cohesive and on-tone for healthcare. Approved.",
  evidence: [
    { criterion: "Mood board + palette + type approved", check_type: "human_required", passed: true, detail: "Client approved direction." },
  ],
  reviewed_by: "ai",
  created_at: daysFromNow(-3),
};

export const mockCharter: Charter = {
  id: "charter_logo",
  order_id: mockOrder.id,
  task_id: "task_logo",
  version: 1,
  snapshot: {
    scope: "Design the HealthTrack logo consistent with approved brand direction.",
    deliverables: [{ name: "Logo", format: "SVG + PNG", required: true }],
    acceptance_criteria: [
      { criterion: "Logo delivered in SVG and PNG", check_type: "deterministic", rule: "files_include_format(['svg','png'])" },
    ],
    price: 2000,
    deadline: daysFromNow(2),
    revision_limit: 2,
    out_of_scope: ["Brand guide", "Social templates"],
  },
  mutual_start_at: null,
  created_at: hoursFromNow(-4),
};

export const mockTaskPacket: TaskPacket = {
  id: "packet_logo",
  task_id: "task_logo",
  charter_id: mockCharter.id,
  version: 1,
  brief:
    "Deliver a clean HealthTrack logo (SVG + PNG) that matches the approved brand direction and works as a favicon.",
  checklist: [
    {
      id: "chk_1",
      label: "Export logo as SVG and PNG",
      source_criterion: "Logo delivered in SVG and PNG",
      required: true,
      done: false,
    },
    {
      id: "chk_2",
      label: "Confirm mark works at favicon size",
      required: true,
      done: false,
    },
    {
      id: "chk_3",
      label: "Align with approved brand direction",
      source_criterion: "Matches approved brand direction",
      required: true,
      done: false,
    },
  ],
  client_inputs: ["company_name", "tagline", "reference_sites"],
  dependencies: ["Brand direction"],
  references: [],
  created_at: hoursFromNow(-4),
};

export const mockDiscussion: DiscussionThread = {
  id: "thread_logo",
  task_id: "task_logo",
  order_id: mockOrder.id,
  status: "active",
  messages: [
    {
      id: "msg_1",
      thread_id: "thread_logo",
      sender_id: "system",
      sender_name: "Orchestra",
      body: "Charter locked. This room is scoped to the logo task.",
      message_type: "system",
      attachments: [],
      scope_flagged: false,
      created_at: hoursFromNow(-4),
    },
    {
      id: "msg_2",
      thread_id: "thread_logo",
      sender_id: mockClient.id,
      sender_name: "Ananya Sharma",
      body: "Please keep the mark simple enough to work as a favicon.",
      message_type: "clarification",
      attachments: [],
      scope_flagged: false,
      created_at: hoursFromNow(-3),
    },
    {
      id: "msg_3",
      thread_id: "thread_logo",
      sender_id: mockClient.id,
      sender_name: "Ananya Sharma",
      body: "Also add a blog section to the landing page.",
      message_type: "scope_change_request",
      attachments: [],
      scope_flagged: true,
      created_at: hoursFromNow(-2),
    },
  ],
};

export const mockDeliveryBundle: DeliveryBundle = {
  id: "bundle_healthtrack",
  order_id: mockOrder.id,
  assets: [
    { name: "Logo (SVG)", url: "https://files.example/logo.svg", type: "image/svg+xml" },
    { name: "Brand guide", url: "https://files.example/brand-guide.pdf", type: "application/pdf" },
    { name: "Figma UI", url: "https://figma.com/file/healthtrack", type: "figma" },
    { name: "Live site", url: "https://healthtrack.example", type: "url" },
  ],
  qa_summary: "All acceptance criteria passed. Lighthouse 82 on mobile.",
  delivered_at: hoursFromNow(-1),
  accepted_at: null,
  accepted_by: null,
};

// ----------------------------------------------------------------------------
// Worker inbox + notifications
// ----------------------------------------------------------------------------

export const mockNotifications: AppNotification[] = [
  {
    id: "ntf_1",
    user_id: mockWorkerMe.user_id,
    type: "priority_granted",
    title: "You have priority",
    body: "You're first in line for the HealthTrack logo. Start within 20h.",
    ref_type: "task",
    ref_id: "task_logo",
    read: false,
    created_at: hoursFromNow(-4),
  },
];
