"""
App Components API endpoints.

App Components enable building custom apps that extend Asana's functionality
through modal forms, rule actions, lookups, and widgets.

This includes:
- Modal forms: 4 APIs
- Rule actions: 5 APIs  
- Lookups: 2 APIs
- Widgets: 1 API
"""
from typing import Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import generate_gid
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()
modal_forms_router = APIRouter()
rule_actions_router = APIRouter()
lookups_router = APIRouter()
widgets_router = APIRouter()


# ============================================================================
# MODAL FORMS (4 APIs)
# ============================================================================

class ModalFormModel:
    def __init__(self, gid: str, title: str, submit_button_text: str = "Submit",
                 on_submit_callback: str = None):
        self.gid = gid
        self.resource_type = "modal_form"
        self.title = title
        self.submit_button_text = submit_button_text
        self.on_submit_callback = on_submit_callback

    def to_response(self):
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "title": self.title,
            "submit_button_text": self.submit_button_text,
            "on_submit_callback": self.on_submit_callback,
        }


_modal_forms = {}


@modal_forms_router.get("")
async def get_modal_forms(
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get all modal forms.
    
    Returns all modal form configurations for the app.
    """
    forms = list(_modal_forms.values())
    
    parser = OptFieldsParser(params.opt_fields)
    form_responses = [parser.filter(f.to_response()) for f in forms]
    
    paginated = paginate(
        form_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/modal_forms",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@modal_forms_router.post("")
async def create_modal_form(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new modal form.
    
    Creates a modal form configuration that can be displayed to users.
    """
    form_data = data.get("data", {})
    
    title = form_data.get("title")
    if not title:
        raise ValidationError("title is required")
    
    form = ModalFormModel(
        gid=generate_gid(),
        title=title,
        submit_button_text=form_data.get("submit_button_text", "Submit"),
        on_submit_callback=form_data.get("on_submit_callback"),
    )
    
    _modal_forms[form.gid] = form
    
    return wrap_response(form.to_response())


@modal_forms_router.get("/{modal_form_gid}")
async def get_modal_form(
    modal_form_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a modal form by GID.
    
    Returns the modal form configuration.
    """
    form = _modal_forms.get(modal_form_gid)
    
    if not form:
        raise NotFoundError("ModalForm", modal_form_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(form.to_response()))


@modal_forms_router.post("/{modal_form_gid}/submit")
async def submit_modal_form(
    modal_form_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Submit a modal form.
    
    Processes the form submission and triggers the callback.
    """
    form = _modal_forms.get(modal_form_gid)
    
    if not form:
        raise NotFoundError("ModalForm", modal_form_gid)
    
    submission_data = data.get("data", {})
    
    return wrap_response({
        "gid": generate_gid(),
        "resource_type": "modal_form_submission",
        "form": {"gid": modal_form_gid, "resource_type": "modal_form"},
        "values": submission_data,
        "submitted_at": datetime.utcnow().isoformat(),
    })


# ============================================================================
# RULE ACTIONS (5 APIs)
# ============================================================================

class RuleActionModel:
    def __init__(self, gid: str, name: str, action_type: str,
                 resource_url: str = None):
        self.gid = gid
        self.resource_type = "rule_action"
        self.name = name
        self.action_type = action_type
        self.resource_url = resource_url

    def to_response(self):
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "name": self.name,
            "action_type": self.action_type,
            "resource_url": self.resource_url,
        }


_rule_actions = {}


@rule_actions_router.get("")
async def get_rule_actions(
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get all rule actions.
    
    Returns all rule action configurations available for automation.
    """
    actions = list(_rule_actions.values())
    
    parser = OptFieldsParser(params.opt_fields)
    action_responses = [parser.filter(a.to_response()) for a in actions]
    
    paginated = paginate(
        action_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/rule_actions",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@rule_actions_router.post("")
async def create_rule_action(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new rule action.
    
    Creates a rule action that can be triggered by automation rules.
    """
    action_data = data.get("data", {})
    
    name = action_data.get("name")
    if not name:
        raise ValidationError("name is required")
    
    action = RuleActionModel(
        gid=generate_gid(),
        name=name,
        action_type=action_data.get("action_type", "custom"),
        resource_url=action_data.get("resource_url"),
    )
    
    _rule_actions[action.gid] = action
    
    return wrap_response(action.to_response())


@rule_actions_router.get("/{rule_action_gid}")
async def get_rule_action(
    rule_action_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a rule action by GID.
    
    Returns the rule action configuration.
    """
    action = _rule_actions.get(rule_action_gid)
    
    if not action:
        raise NotFoundError("RuleAction", rule_action_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(action.to_response()))


@rule_actions_router.put("/{rule_action_gid}")
async def update_rule_action(
    rule_action_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a rule action.
    
    Updates the rule action configuration.
    """
    action = _rule_actions.get(rule_action_gid)
    
    if not action:
        raise NotFoundError("RuleAction", rule_action_gid)
    
    update_data = data.get("data", {})
    
    if "name" in update_data:
        action.name = update_data["name"]
    if "action_type" in update_data:
        action.action_type = update_data["action_type"]
    if "resource_url" in update_data:
        action.resource_url = update_data["resource_url"]
    
    return wrap_response(action.to_response())


@rule_actions_router.post("/{rule_action_gid}/run")
async def run_rule_action(
    rule_action_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Run a rule action.
    
    Executes the rule action with the provided context and data.
    """
    action = _rule_actions.get(rule_action_gid)
    
    if not action:
        raise NotFoundError("RuleAction", rule_action_gid)
    
    context = data.get("data", {})
    
    return wrap_response({
        "gid": generate_gid(),
        "resource_type": "rule_action_run",
        "action": {"gid": rule_action_gid, "resource_type": "rule_action"},
        "status": "completed",
        "executed_at": datetime.utcnow().isoformat(),
    })


# ============================================================================
# LOOKUPS (2 APIs)
# ============================================================================

class LookupModel:
    def __init__(self, gid: str, name: str, resource_url: str):
        self.gid = gid
        self.resource_type = "lookup"
        self.name = name
        self.resource_url = resource_url

    def to_response(self):
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "name": self.name,
            "resource_url": self.resource_url,
        }


_lookups = {}


@lookups_router.get("")
async def get_lookups(
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get all lookups.
    
    Returns all lookup configurations for external data integration.
    """
    lookups = list(_lookups.values())
    
    parser = OptFieldsParser(params.opt_fields)
    lookup_responses = [parser.filter(l.to_response()) for l in lookups]
    
    paginated = paginate(
        lookup_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/lookups",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@lookups_router.post("/{lookup_gid}/run")
async def run_lookup(
    lookup_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Run a lookup.
    
    Executes the lookup and returns matching results from the external source.
    """
    lookup = _lookups.get(lookup_gid)
    
    if not lookup:
        raise NotFoundError("Lookup", lookup_gid)
    
    query = data.get("data", {}).get("query", "")
    
    return {
        "data": {
            "header": "Results",
            "items": [],
        }
    }


# ============================================================================
# WIDGETS (1 API)
# ============================================================================

@widgets_router.get("/{widget_gid}")
async def get_widget(
    widget_gid: str,
    task: Optional[str] = Query(None, description="Task GID for context"),
    project: Optional[str] = Query(None, description="Project GID for context"),
    workspace: Optional[str] = Query(None, description="Workspace GID"),
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get widget metadata.
    
    Returns the widget configuration and data to render in the Asana UI.
    Widgets can display custom content in task panels, project overviews, etc.
    """
    return wrap_response({
        "gid": widget_gid,
        "resource_type": "widget",
        "metadata": {
            "title": "Widget",
            "subtitle": "Custom widget content",
            "fields": [],
        },
        "template": "summary_with_details_v0",
    })

