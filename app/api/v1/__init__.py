from fastapi import APIRouter

from app.api.v1 import (
    users,
    workspaces,
    teams,
    projects,
    sections,
    tasks,
    stories,
    attachments,
    tags,
    custom_fields,
    custom_field_settings,
    custom_types,
    portfolios,
    goals,
    webhooks,
    events,
    batch,
    typeahead,
    jobs,
    user_task_lists,
    project_templates,
    task_templates,
    audit_logs,
    organization_exports,
    exports,
    time_periods,
    time_tracking_entries,
    allocations,
    access_requests,
    budgets,
    memberships,
    rates,
    reactions,
    rules,
    app_components,
)

router = APIRouter()

# Core resources
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(workspaces.router, prefix="/workspaces", tags=["Workspaces"])
router.include_router(teams.router, prefix="/teams", tags=["Teams"])
router.include_router(projects.router, prefix="/projects", tags=["Projects"])
router.include_router(sections.router, prefix="/sections", tags=["Sections"])
router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
router.include_router(stories.router, prefix="/stories", tags=["Stories"])
router.include_router(attachments.router, prefix="/attachments", tags=["Attachments"])
router.include_router(tags.router, prefix="/tags", tags=["Tags"])

# Advanced features
router.include_router(custom_fields.router, prefix="/custom_fields", tags=["Custom Fields"])
router.include_router(custom_field_settings.router, prefix="/custom_field_settings", tags=["Custom Field Settings"])
router.include_router(custom_types.router, prefix="/custom_types", tags=["Custom Types"])
router.include_router(portfolios.router, prefix="/portfolios", tags=["Portfolios"])
router.include_router(goals.router, prefix="/goals", tags=["Goals"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
router.include_router(events.router, prefix="/events", tags=["Events"])
router.include_router(batch.router, prefix="/batch", tags=["Batch API"])

# Additional features
router.include_router(typeahead.router, prefix="/typeahead", tags=["Typeahead"])
router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
router.include_router(user_task_lists.router, prefix="/user_task_lists", tags=["User Task Lists"])
router.include_router(project_templates.router, prefix="/project_templates", tags=["Project Templates"])
router.include_router(task_templates.router, prefix="/task_templates", tags=["Task Templates"])

# Enterprise features
router.include_router(audit_logs.router, prefix="/audit_log_events", tags=["Audit Log API"])
router.include_router(organization_exports.router, prefix="/organization_exports", tags=["Organization Exports"])
router.include_router(exports.router, prefix="/exports", tags=["Exports"])
router.include_router(time_periods.router, prefix="/time_periods", tags=["Time Periods"])
router.include_router(time_tracking_entries.router, prefix="/time_tracking_entries", tags=["Time Tracking Entries"])

# Resource management
router.include_router(allocations.router, prefix="/allocations", tags=["Allocations"])
router.include_router(access_requests.router, prefix="/access_requests", tags=["Access Requests"])
router.include_router(budgets.router, prefix="/budgets", tags=["Budgets"])
router.include_router(memberships.router, prefix="/memberships", tags=["Memberships"])
router.include_router(rates.router, prefix="/rates", tags=["Rates"])
router.include_router(reactions.router, prefix="/reactions", tags=["Reactions"])
router.include_router(rules.router, prefix="/rules", tags=["Rules"])

# Workspace-specific endpoints for memberships
router.include_router(
    workspaces.membership_router, 
    prefix="/workspace_memberships", 
    tags=["Workspace Memberships"]
)

# Team membership endpoints
router.include_router(
    teams.membership_router,
    prefix="/team_memberships",
    tags=["Team Memberships"]
)

# Project membership endpoints  
router.include_router(
    projects.membership_router,
    prefix="/project_memberships",
    tags=["Project Memberships"]
)

# Portfolio membership endpoints
router.include_router(
    portfolios.membership_router,
    prefix="/portfolio_memberships",
    tags=["Portfolio Memberships"]
)

# Goal relationship endpoints
router.include_router(
    goals.relationship_router,
    prefix="/goal_relationships",
    tags=["Goal Relationships"]
)

# Goal membership endpoints
router.include_router(
    goals.membership_router,
    prefix="/goal_memberships",
    tags=["Goal Memberships"]
)

# Status updates
router.include_router(
    goals.status_router,
    prefix="/status_updates",
    tags=["Status Updates"]
)

# Project statuses
router.include_router(
    projects.status_router,
    prefix="/project_statuses",
    tags=["Project Statuses"]
)

# Project briefs
router.include_router(
    projects.brief_router,
    prefix="/project_briefs",
    tags=["Project Briefs"]
)

# App Components
router.include_router(
    app_components.modal_forms_router,
    prefix="/modal_forms",
    tags=["Modal Forms"]
)

router.include_router(
    app_components.rule_actions_router,
    prefix="/rule_actions",
    tags=["Rule Actions"]
)

router.include_router(
    app_components.lookups_router,
    prefix="/lookups",
    tags=["Lookups"]
)

router.include_router(
    app_components.widgets_router,
    prefix="/widgets",
    tags=["Widgets"]
)
