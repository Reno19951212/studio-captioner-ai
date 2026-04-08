import pytest
from app.ws.handlers import progress_manager


def test_progress_manager_subscribe_unsubscribe():
    assert progress_manager is not None
    assert hasattr(progress_manager, "subscribe")
    assert hasattr(progress_manager, "unsubscribe")
    assert hasattr(progress_manager, "broadcast_task")
    assert hasattr(progress_manager, "broadcast_queue")
