"""Explicit confirmation gate for assistant-initiated write actions."""


def confirm_action(tool_name: str, arguments: dict, auto_approve: bool = False) -> bool:
    """Return whether the student explicitly approved this assistant action.

    Keeping this gate separate makes it impossible for a write tool to run
    merely because a model requested it.
    """
    if tool_name != "save_job_or_event":
        return True
    return auto_approve
