from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
import json

from pydantic import BaseModel


class EventType(str, Enum):
    """Event types for the Asana event system."""
    ADDED = "added"
    CHANGED = "changed"
    DELETED = "deleted"
    REMOVED = "removed"
    UNDELETED = "undeleted"


class EventAction(str, Enum):
    """Specific actions that trigger events."""
    # Task events
    TASK_ADDED = "task_added"
    TASK_CHANGED = "task_changed"
    TASK_DELETED = "task_deleted"
    TASK_UNDELETED = "task_undeleted"
    
    # Project events
    PROJECT_ADDED = "project_added"
    PROJECT_CHANGED = "project_changed"
    PROJECT_DELETED = "project_deleted"
    
    # Story events
    STORY_ADDED = "story_added"
    STORY_CHANGED = "story_changed"
    STORY_DELETED = "story_deleted"
    
    # Section events
    SECTION_ADDED = "section_added"
    SECTION_CHANGED = "section_changed"
    SECTION_DELETED = "section_deleted"
    
    # Tag events
    TAG_ADDED = "tag_added"
    TAG_CHANGED = "tag_changed"
    TAG_DELETED = "tag_deleted"


class Event(BaseModel):
    """Model for an event in the event system."""
    gid: str
    resource_type: str
    resource_gid: str
    parent: Optional[Dict[str, Any]] = None
    action: str
    user_gid: Optional[str] = None
    created_at: datetime
    change: Optional[Dict[str, Any]] = None


class EventStore:
    """
    In-memory event store for tracking changes.
    In production, this would be backed by a database or message queue.
    """
    
    def __init__(self, max_events: int = 10000):
        self._events: Dict[str, List[Event]] = {}  # resource_gid -> events
        self._sync_tokens: Dict[str, str] = {}  # resource_gid -> sync_token
        self._max_events = max_events
        self._lock = asyncio.Lock()
    
    async def add_event(
        self,
        resource_type: str,
        resource_gid: str,
        action: str,
        user_gid: Optional[str] = None,
        parent: Optional[Dict[str, Any]] = None,
        change: Optional[Dict[str, Any]] = None,
    ) -> Event:
        """Add an event to the store."""
        from app.core.security import generate_gid
        
        async with self._lock:
            event = Event(
                gid=generate_gid(),
                resource_type=resource_type,
                resource_gid=resource_gid,
                parent=parent,
                action=action,
                user_gid=user_gid,
                created_at=datetime.utcnow(),
                change=change,
            )
            
            if resource_gid not in self._events:
                self._events[resource_gid] = []
            
            self._events[resource_gid].append(event)
            
            # Trim old events if exceeding max
            if len(self._events[resource_gid]) > self._max_events:
                self._events[resource_gid] = self._events[resource_gid][-self._max_events:]
            
            # Update sync token
            self._sync_tokens[resource_gid] = event.gid
            
            return event
    
    async def get_events(
        self,
        resource_gid: str,
        sync_token: Optional[str] = None,
    ) -> tuple[List[Event], str, bool]:
        """
        Get events for a resource since the given sync token.
        Returns (events, new_sync_token, has_more).
        """
        async with self._lock:
            events = self._events.get(resource_gid, [])
            
            if sync_token:
                # Find events after the sync token
                found_token = False
                filtered_events = []
                for event in events:
                    if found_token:
                        filtered_events.append(event)
                    elif event.gid == sync_token:
                        found_token = True
                events = filtered_events
            
            new_sync_token = self._sync_tokens.get(resource_gid, "")
            has_more = len(events) > 100  # Asana limits to 100 events per request
            
            return events[:100], new_sync_token, has_more
    
    async def get_sync_token(self, resource_gid: str) -> str:
        """Get the current sync token for a resource."""
        async with self._lock:
            return self._sync_tokens.get(resource_gid, "sync:0")


# Global event store instance
event_store = EventStore()

