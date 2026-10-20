"""
Thread-safe Async Task Dispatcher for CustomTkinter.
Ensures network requests (FastAPI calls) run on background threads without blocking the UI,
while all GUI updates, widget mutations, and state changes are dispatched safely on the main thread via queue.
Completely eliminates Python 3.12 'RuntimeError: main thread is not in main loop'.
"""
import queue
import threading
from typing import Callable, Any, Optional

_gui_queue: queue.Queue = queue.Queue()
_root_window = None


def init_async(root):
    """Initialize the GUI event pump on the root CustomTkinter window."""
    global _root_window
    _root_window = root
    _poll_gui_queue()


def _poll_gui_queue():
    global _root_window
    if _root_window is None:
        return

    try:
        while not _gui_queue.empty():
            callback, args, kwargs = _gui_queue.get_nowait()
            try:
                callback(*args, **kwargs)
            except Exception:
                pass
    except Exception:
        pass

    try:
        _root_window.after(40, _poll_gui_queue)
    except Exception:
        pass


def run_in_background(
    task_fn: Callable[[], Any],
    on_success: Callable[[Any], None],
    on_error: Optional[Callable[[Exception], None]] = None
):
    """
    Executes task_fn on a daemon background thread.
    Dispatches on_success(result) or on_error(exception) to the main GUI thread.
    """
    def _worker():
        try:
            result = task_fn()
            _gui_queue.put((on_success, (result,), {}))
        except Exception as exc:
            if on_error:
                _gui_queue.put((on_error, (exc,), {}))

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread
