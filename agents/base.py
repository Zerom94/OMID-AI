"""OMID AI - Base Agent Interface"""
from __future__ import annotations
import abc
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from core.db import get_db

@dataclass
class Task:
    id: str
    description: str
    agent_id: str
    priority: int = 5
    status: str = "pending"
    dependencies: list[str] = field(default_factory=list)
    result: Optional[dict] = None
    error: Optional[str] = None
    retry_count: int = 0
    created_at: str = ""
    completed_at: str = ""
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

@dataclass
class Result:
    task_id: str
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class BaseAgent(abc.ABC):
    name: str = "BaseAgent"
    display_name: str = "Base Agent"
    
    def __init__(self, config=None, memory=None):
        self.config = config or {}
        self.memory = memory or get_db()
        self.log_callback = None

    @abc.abstractmethod
    async def execute(self, task: Task) -> Result:
        raise NotImplementedError

    def log_event(self, event_type: str, data: dict):
        try:
            self.memory.log_event(self.name, event_type, data)
        except Exception:
            pass
        if self.log_callback:
            try:
                if asyncio.iscoroutinefunction(self.log_callback):
                    asyncio.create_task(self.log_callback(self.name, event_type, data))
                else:
                    self.log_callback(self.name, event_type, data)
            except Exception:
                pass
