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
    time_periods,
    time_tracking_entries,
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
router.include_router(portfolios.router, prefix="/portfolios", tags=["Portfolios"])
router.include_router(goals.router, prefix="/goals", tags=["Goals"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
router.include_router(events.router, prefix="/events", tags=["Events"])
router.include_router(batch.router, prefix="/batch", tags=["Batch"])

# Additional features
router.include_router(typeahead.router, prefix="/typeahead", tags=["Typeahead"])
router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
router.include_router(user_task_lists.router, prefix="/user_task_lists", tags=["User Task Lists"])
router.include_router(project_templates.router, prefix="/project_templates", tags=["Project Templates"])
router.include_router(task_templates.router, prefix="/task_templates", tags=["Task Templates"])

# Enterprise features
router.include_router(audit_logs.router, prefix="/audit_log_events", tags=["Audit Logs"])
router.include_router(organization_exports.router, prefix="/organization_exports", tags=["Organization Exports"])
router.include_router(time_periods.router, prefix="/time_periods", tags=["Time Periods"])
router.include_router(time_tracking_entries.router, prefix="/time_tracking_entries", tags=["Time Tracking Entries"])

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

