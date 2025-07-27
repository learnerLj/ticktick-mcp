"""Data models for TickTick entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class TaskStatus(Enum):
    """Task status enumeration."""
    ACTIVE = 0
    COMPLETED = 2


class Priority(Enum):
    """Task priority enumeration."""
    NONE = 0
    LOW = 1
    MEDIUM = 3
    HIGH = 5


class ViewMode(Enum):
    """Project view mode enumeration."""
    LIST = "list"
    KANBAN = "kanban"
    TIMELINE = "timeline"


@dataclass
class SubTask:
    """Represents a subtask within a task."""
    id: str
    title: str
    status: int = 0
    order: int = 0
    
    @property
    def is_completed(self) -> bool:
        """Check if subtask is completed."""
        return self.status == 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubTask":
        """Create SubTask from dictionary."""
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            status=data.get("status", 0),
            order=data.get("order", 0),
        )


@dataclass
class Task:
    """Represents a TickTick task."""
    id: str
    title: str
    project_id: Optional[str] = None
    content: Optional[str] = None
    status: TaskStatus = TaskStatus.ACTIVE
    priority: Priority = Priority.NONE
    start_date: Optional[str] = None
    due_date: Optional[str] = None
    is_all_day: bool = False
    subtasks: List[SubTask] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_time: Optional[str] = None
    modified_time: Optional[str] = None

    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == TaskStatus.COMPLETED

    @property
    def priority_name(self) -> str:
        """Get human-readable priority name."""
        priority_map = {
            Priority.NONE: "None",
            Priority.LOW: "Low", 
            Priority.MEDIUM: "Medium",
            Priority.HIGH: "High"
        }
        return priority_map.get(self.priority, "Unknown")

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        data = {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "priority": self.priority.value,
            "isAllDay": self.is_all_day,
        }
        
        if self.project_id:
            data["projectId"] = self.project_id
        if self.content:
            data["content"] = self.content
        if self.start_date:
            data["startDate"] = self.start_date
        if self.due_date:
            data["dueDate"] = self.due_date
        if self.subtasks:
            data["items"] = [subtask.to_dict() for subtask in self.subtasks]
        if self.tags:
            data["tags"] = self.tags
        if self.created_time:
            data["createdTime"] = self.created_time
        if self.modified_time:
            data["modifiedTime"] = self.modified_time
            
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create Task from dictionary."""
        subtasks = []
        if "items" in data:
            subtasks = [SubTask.from_dict(item) for item in data["items"]]
            
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            project_id=data.get("projectId"),
            content=data.get("content"),
            status=TaskStatus(data.get("status", 0)),
            priority=Priority(data.get("priority", 0)),
            start_date=data.get("startDate"),
            due_date=data.get("dueDate"),
            is_all_day=data.get("isAllDay", False),
            subtasks=subtasks,
            tags=data.get("tags", []),
            created_time=data.get("createdTime"),
            modified_time=data.get("modifiedTime"),
        )


@dataclass
class Project:
    """Represents a TickTick project."""
    id: str
    name: str
    color: str = "#F18181"
    view_mode: ViewMode = ViewMode.LIST
    kind: str = "TASK"
    closed: bool = False
    group_id: Optional[str] = None
    sort_order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "viewMode": self.view_mode.value,
            "kind": self.kind,
            "closed": self.closed,
            "groupId": self.group_id,
            "sortOrder": self.sort_order,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        """Create Project from dictionary."""
        view_mode = ViewMode.LIST
        if "viewMode" in data:
            try:
                view_mode = ViewMode(data["viewMode"])
            except ValueError:
                pass  # Use default if invalid
                
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            color=data.get("color", "#F18181"),
            view_mode=view_mode,
            kind=data.get("kind", "TASK"),
            closed=data.get("closed", False),
            group_id=data.get("groupId"),
            sort_order=data.get("sortOrder", 0),
        )


@dataclass
class TaskFilter:
    """Filter criteria for task queries."""
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    project_id: Optional[str] = None
    query: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = 50

    def to_params(self) -> Dict[str, str]:
        """Convert filter to query parameters."""
        params = {}
        
        if self.status:
            params["status"] = str(self.status.value)
        if self.priority:
            params["priority"] = str(self.priority.value)
        if self.project_id:
            params["projectId"] = self.project_id
        if self.query:
            params["q"] = self.query
        if self.start_date:
            params["startDate"] = self.start_date
        if self.end_date:
            params["endDate"] = self.end_date
        if self.limit:
            params["limit"] = str(self.limit)
            
        return params