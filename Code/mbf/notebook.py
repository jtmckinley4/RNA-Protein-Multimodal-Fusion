"""Helpers for presenting shared code inside notebooks."""

from __future__ import annotations

import inspect


def show_source(*objects):
    """Display the source of functions or classes from mbf as a Python code block.

    Notebooks call this beside an explanation so the code it describes is visible
    without being copied into the notebook.
    """
    from IPython.display import Markdown, display

    blocks = [f"```python\n{inspect.getsource(o).rstrip()}\n```" for o in objects]
    display(Markdown("\n\n".join(blocks)))
