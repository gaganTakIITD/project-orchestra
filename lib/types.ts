/**
 * Project Orchestra — Shared Contract Types
 * =========================================
 * The single source of truth for data shapes across the app.
 *
 * These mirror `docs/Project_Orchestra_Technical_Spec.md` (§4 DB schema, §5 state
 * machines, §7 API contract, §8 AI agents). Fields use snake_case to match the
 * JSON the FastAPI backend will return, so the frontend needs no translation
 * layer when we swap mocks -> real API (see `lib/api.ts`).
 *
 * OWNERSHIP: this file is owned by the "thin frontend" (Cursor) side.
 * v0 imports these types; it should not redefine them.
 */

// ----------------------------------------------------------------------------
// Identity & Trust (Spec §4.1)
// ----------------------------------------------------------------------------

export type UserRole = "client" | "worker" | "admin";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  profile_photo_url?: string | null;
  phone?: string | null;
  is_active: boolean;
  email_verified: boolean;
  created_at: string;
}

export type CommunityType = "design" | "tech" | "both";
export type AvailabilityStatus = "available" | "busy" | "unavailable";
export type SellerLevel = "new" | "rising" | "trusted" | "top";
export type Proficiency = "beginner" | "intermediate" | "advanced" | "expert";

export interface WorkerProfile {
  user_id: string;
  full_name: string;
  profile_photo_url?: string | null;
  community_type: CommunityType;
  headline: string;
  bio: string;
  availability_status: AvailabilityStatus;
  weekly_hours_available: number;
  max_concurrent_tasks: number;
  payout_min?: number | null;
  payout_max?: number | null;
  campus_verified: boolean;
  is_active: boolean;
  profile_completion_pct: number;
  github_url?: string | null;
  figma_url?: string | null;
  behance_url?: string | null;
  linkedin_url?: string | null;
  skills: WorkerSkill[];
  tools: WorkerTool[];
  task_types: WorkerTaskType[];
  portfolio: PortfolioItem[];
  stats?: WorkerStats;
}

export interface WorkerStats {
  worker_id: string;
  tasks_completed: number;
  on_time_pct: number;
  avg_qa_score: number;
  avg_rating: number;
  response_time_hours?: number | null;
  seller_level: SellerLevel;
  last_active_at?: string | null;
}

// ----------------------------------------------------------------------------
// Taxonomy — shared language (Spec §4.2)
// ----------------------------------------------------------------------------

export type SkillCategory = "design" | "frontend" | "backend" | "ai_ml" | "other";

export interface Skill {
  id: string;
  name: string;
  slug: string;
  category: SkillCategory;
}

export interface Tool {
  id: string;
  name: string;
  slug: string;
  category?: string;
}

export interface TaskType {
  id: string;
  name: string;
  slug: string;
  community_type: CommunityType;
  description?: string;
  typical_hours?: number;
}

export interface WorkerSkill {
  skill_id: string;
  name: string;
  proficiency: Proficiency;
  years_experience?: number;
}

export interface WorkerTool {
  tool_id: string;
  name: string;
  proficiency: Proficiency;
}

export interface WorkerTaskType {
  task_type_id: string;
  name: string;
  slug: string;
  proficiency: Proficiency;
}

export interface PortfolioItem {
  id: string;
  worker_id: string;
  title: string;
  description?: string;
  category?: string;
  cover_image_url?: string | null;
  project_url?: string | null;
  tags: string[];
  tools_used: string[];
  is_featured: boolean;
}

// ----------------------------------------------------------------------------
// Catalog & Quoting (Spec §4.3)
// ----------------------------------------------------------------------------

export type SkuCategory = "design" | "tech" | "combined";

export interface OutcomeSku {
  id: string;
  slug: string;
  name: string;
  category: SkuCategory;
  description: string;
  base_price: number;
  typical_days: number;
  revision_limit: number;
}

export interface Intent {
  id: string;
  client_id: string;
  raw_text: string;
  attachments: string[];
  status: "captured" | "compiling" | "needs_clarification" | "compiled";
  clarifying_questions?: string[];
  created_at: string;
}

/** How a single acceptance criterion is verified (Spec §16 model refinement #1). */
export type CheckType = "deterministic" | "ai_judged" | "human_required";

export interface AcceptanceCriterion {
  criterion: string;
  check_type: CheckType;
  /** deterministic rule expression, or an AI rubric string */
  rule?: string;
  rubric?: string;
}

export interface Deliverable {
  name: string;
  format: string;
  required: boolean;
}

/** Risk tier L0–L3 (Diagrams G2). Governs how much human oversight QA needs. */
export type RiskTier = "L0" | "L1" | "L2" | "L3";

/** Output of the Spec Compiler AI node (Spec §8.2). Frozen at order confirm. */
export interface OutcomeSpec {
  id: string;
  intent_id: string;
  sku_id?: string | null;
  outcome_statement: string;
  deliverables: Deliverable[];
  acceptance_criteria: AcceptanceCriterion[];
  in_scope: string[];
  out_of_scope: string[];
  assumptions: string[];
  client_inputs_required: string[];
  mapped_task_types: string[];
  risk_tier: RiskTier;
  version: number;
  frozen_at?: string | null;
}

/** In-progress spec during scope chat — same schema, not yet persisted/frozen. */
export interface OutcomeSpecDraft {
  outcome_statement: string;
  deliverables: Deliverable[];
  acceptance_criteria: AcceptanceCriterion[];
  in_scope: string[];
  out_of_scope: string[];
  assumptions: string[];
  client_inputs_required: string[];
  mapped_task_types: string[];
  risk_tier: RiskTier;
  workflow_summary?: string;
  sku_id?: string | null;
  version: number;
}

export type QuoteStatus = "issued" | "accepted" | "expired" | "superseded";

export interface Quote {
  id: string;
  spec_id: string;
  client_id: string;
  price: number;
  deadline: string;
  revision_limit: number;
  status: QuoteStatus;
  valid_until: string;
  ai_confidence?: number;
  ai_rationale?: string;
  created_at: string;
}

// ----------------------------------------------------------------------------
// Orders & Contracts (Spec §4.4, §5.1)
// ----------------------------------------------------------------------------

export type OrderStatus =
  | "confirmed"
  | "assembling_team"
  | "delivery_active"
  | "under_quality_check"
  | "delivered"
  | "closed"
  | "amendment_pending"
  | "escalated"
  | "cancelled";

export interface OutcomeOrder {
  id: string;
  client_id: string;
  quote_id: string;
  spec_id: string;
  sku_id?: string | null;
  status: OrderStatus;
  price: number;
  deadline: string;
  revision_limit: number;
  progress_pct: number;
  created_at: string;
  updated_at: string;
}

export interface Charter {
  id: string;
  order_id: string;
  task_id?: string | null;
  version: number;
  /** Frozen snapshot of scope + price + deadline + acceptance criteria. */
  snapshot: {
    scope: string;
    deliverables: Deliverable[];
    acceptance_criteria: AcceptanceCriterion[];
    price: number;
    deadline: string;
    revision_limit: number;
    out_of_scope: string[];
  };
  mutual_start_at?: string | null;
  created_at: string;
}

export type AmendmentStatus = "requested" | "priced" | "approved" | "rejected";

export interface Amendment {
  id: string;
  order_id: string;
  charter_id: string;
  requested_by: string;
  delta_description: string;
  price_delta: number;
  time_delta_hours: number;
  status: AmendmentStatus;
  created_at: string;
}

// ----------------------------------------------------------------------------
// Fulfillment — DAG + Tasks (Spec §4.5, §5.2)
// ----------------------------------------------------------------------------

export type TaskStatus =
  | "blocked"
  | "ready"
  | "invited"
  | "interest_pool"
  | "priority_active"
  | "start_requested"
  | "mutual_start"
  | "in_progress"
  | "submitted"
  | "rework"
  | "completed"
  | "cancelled"
  | "released";

export interface FulfillmentTask {
  id: string;
  plan_id: string;
  order_id: string;
  task_type_id: string;
  task_type_slug: string;
  title: string;
  description?: string;
  acceptance_criteria: AcceptanceCriterion[];
  status: TaskStatus;
  sequence_order: number;
  payout_amount: number;
  deadline?: string | null;
  assigned_worker_id?: string | null;
  revision_count: number;
  revision_limit: number;
  priority_window_ends?: string | null;
  depends_on: string[];
  started_at?: string | null;
  completed_at?: string | null;
}

export interface FulfillmentMilestone {
  name: string;
  task_ids: string[];
  client_label: string;
}

export interface FulfillmentPlan {
  id: string;
  order_id: string;
  tasks: FulfillmentTask[];
  milestones: FulfillmentMilestone[];
  critical_path_hours: number;
}

// ----------------------------------------------------------------------------
// Matching — preferences, interest, activation (Spec §4.5, §8.4)
// ----------------------------------------------------------------------------

/** A single ranked worker in the AI Matcher shortlist (Spec §8.4). */
export interface Candidate {
  worker_id: string;
  full_name: string;
  profile_photo_url?: string | null;
  headline: string;
  community_type: CommunityType;
  score: number;
  rationale: string;
  availability: AvailabilityStatus;
  seller_level: SellerLevel;
  tasks_completed: number;
  on_time_pct: number;
}

export interface PreferenceEntry {
  worker_id: string;
  rank: number;
}

export interface PreferenceSet {
  id: string;
  task_id: string;
  order_id: string;
  entries: PreferenceEntry[];
  created_at: string;
}

export type InterestStatus = "accepted" | "declined" | "expired" | "released";

export interface TaskInterest {
  id: string;
  task_id: string;
  worker_id: string;
  status: InterestStatus;
  rank_at_accept?: number;
  accepted_at: string;
}

export type ActivationType = "priority" | "backup";
export type ActivationStatus = "active" | "used" | "expired" | "superseded";

export interface TaskActivation {
  id: string;
  task_id: string;
  worker_id: string;
  activation_type: ActivationType;
  window_starts: string;
  window_ends: string;
  status: ActivationStatus;
}

// ----------------------------------------------------------------------------
// Delivery & Quality (Spec §4.6, §8.5)
// ----------------------------------------------------------------------------

export interface Submission {
  id: string;
  task_id: string;
  worker_id: string;
  notes?: string;
  asset_urls: string[];
  version: number;
  submitted_at: string;
}

export type QAResult = "pass" | "fail";

export interface QACriterionEvidence {
  criterion: string;
  check_type: CheckType;
  passed: boolean;
  detail?: string;
}

export interface QAReview {
  id: string;
  submission_id: string;
  task_id: string;
  result: QAResult;
  score: number;
  confidence: number;
  feedback: string;
  evidence: QACriterionEvidence[];
  reviewed_by: "ai" | string;
  created_at: string;
}

export interface DeliveryBundleAsset {
  name: string;
  url: string;
  type: string;
}

export interface DeliveryBundle {
  id: string;
  order_id: string;
  assets: DeliveryBundleAsset[];
  qa_summary: string;
  delivered_at: string;
  accepted_at?: string | null;
  accepted_by?: string | null;
}

// ----------------------------------------------------------------------------
// Communication (Spec §4.7, §8 Scope Guard)
// ----------------------------------------------------------------------------

export type MessageType =
  | "clarification"
  | "reference"
  | "scope_change_request"
  | "delivery_update"
  | "system";

export interface DiscussionMessage {
  id: string;
  thread_id: string;
  sender_id: string;
  sender_name: string;
  body: string;
  message_type: MessageType;
  attachments: string[];
  scope_flagged: boolean;
  created_at: string;
}

export interface DiscussionThread {
  id: string;
  task_id: string;
  order_id: string;
  status: "active" | "archived";
  messages: DiscussionMessage[];
}

// ----------------------------------------------------------------------------
// Money — client-facing ledger states only (Spec §14; real money is Stage 4+)
// ----------------------------------------------------------------------------

export type LedgerState =
  | "unfunded"
  | "funds_authorized"
  | "milestone_reserved"
  | "worker_payable"
  | "tds_deducted"
  | "payout_released"
  | "refund_pending"
  | "refunded";

export interface Payout {
  id: string;
  worker_id: string;
  task_id: string;
  gross_amount: number;
  tds_amount: number;
  net_amount: number;
  status: "pending" | "processing" | "released" | "failed";
  released_at?: string | null;
}

// ----------------------------------------------------------------------------
// Platform (Spec §4.9)
// ----------------------------------------------------------------------------

export interface AppNotification {
  id: string;
  user_id: string;
  type: string;
  title: string;
  body: string;
  ref_type?: string;
  ref_id?: string;
  read: boolean;
  created_at: string;
}

// ----------------------------------------------------------------------------
// Scope chat — schema-driven extraction (docs/CHAT_SURFACES.md)
// ----------------------------------------------------------------------------

export type ChatAgentType = "spec_compiler" | "pricing" | "matcher";
export type ChatSessionStatus = "active" | "completed" | "archived";

export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  body: string;
  spec_version_after?: number | null;
  created_at: string;
}

export interface ChatSession {
  id: string;
  agent_type: ChatAgentType;
  status: ChatSessionStatus;
  spec_draft: OutcomeSpecDraft;
  spec_version: number;
  completeness_pct: number;
  missing_fields: string[];
  ready_for_quote: boolean;
  messages: ChatMessage[];
  created_at: string;
}

export interface FinalizeChatSessionResult {
  intent_id: string;
  quote_id: string;
}

/** SSE events from POST /chat/sessions/{id}/messages/stream */
export type ChatStreamEvent =
  | { type: "token"; content: string }
  | {
      type: "draft_patch";
      spec_draft: OutcomeSpecDraft;
      spec_version: number;
      completeness_pct: number;
      missing_fields: string[];
      ready_for_quote: boolean;
    }
  | { type: "turn_complete"; session: ChatSession }
  | { type: "error"; message: string };

export type ChatStreamHandlers = {
  onToken?: (content: string) => void;
  onDraftPatch?: (event: Extract<ChatStreamEvent, { type: "draft_patch" }>) => void;
  onTurnComplete?: (session: ChatSession) => void;
  onError?: (message: string) => void;
};
