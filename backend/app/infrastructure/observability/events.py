"""Event bus for pub/sub pattern"""

from typing import Dict, Callable, Any, List
from collections import defaultdict

from app.core.domain.enums import JobEvent


class EventBus:
    """Simple event bus for pub/sub pattern"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to an event type"""
        self._subscribers[event_type].append(handler)
    
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from an event type"""
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
    
    async def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event"""
        for handler in self._subscribers[event_type]:
            try:
                if callable(handler):
                    # Check if handler is async
                    if hasattr(handler, '__call__'):
                        import asyncio
                        if asyncio.iscoroutinefunction(handler):
                            await handler(data)
                        else:
                            handler(data)
            except Exception as e:
                # Log error but don't fail
                print(f"Error in event handler for {event_type}: {e}")


# Global event bus instance
event_bus = EventBus()

