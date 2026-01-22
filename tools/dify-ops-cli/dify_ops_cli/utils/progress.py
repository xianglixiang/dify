"""Progress display utilities."""

import time
from typing import Callable

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)

console = Console()


class TaskProgressTracker:
    """Track and display progress for plugin installation tasks."""

    def __init__(self):
        """Initialize the progress tracker."""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        )

    def __enter__(self):
        """Context manager entry."""
        self.progress.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.progress.__exit__(exc_type, exc_val, exc_tb)

    def add_task(self, description: str, total: int = 100) -> TaskID:
        """Add a new task to track.

        Args:
            description: Task description
            total: Total progress units

        Returns:
            Task ID
        """
        return self.progress.add_task(description, total=total)

    def update(self, task_id: TaskID, advance: int = 0, description: str | None = None):
        """Update task progress.

        Args:
            task_id: Task ID
            advance: Amount to advance progress
            description: New description
        """
        kwargs = {}
        if advance > 0:
            kwargs["advance"] = advance
        if description:
            kwargs["description"] = description

        self.progress.update(task_id, **kwargs)

    def complete(self, task_id: TaskID, description: str | None = None):
        """Mark a task as complete.

        Args:
            task_id: Task ID
            description: Completion message
        """
        if description:
            self.progress.update(task_id, description=description)
        self.progress.update(task_id, completed=True)


def wait_with_progress(
    status_check: Callable[[], tuple[str, float]],
    description: str = "Processing...",
    timeout: int = 300,
    poll_interval: int = 5,
) -> str:
    """Wait for a task with progress display.

    Args:
        status_check: Function that returns (status, progress_percentage)
        description: Task description
        timeout: Maximum wait time in seconds
        poll_interval: Time between status checks in seconds

    Returns:
        Final status

    Raises:
        TimeoutError: If the task times out
        RuntimeError: If the task fails
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(description, total=100)

        start_time = time.time()
        last_status = None

        while time.time() - start_time < timeout:
            try:
                status, progress_pct = status_check()

                # Update description on status change
                if status != last_status:
                    progress.update(task, description=f"{description} - {status}")
                    last_status = status

                # Update progress
                progress.update(task, completed=progress_pct)

                # Check completion
                if status == "completed":
                    progress.update(task, completed=100, description=f"{description} - ✓ Completed")
                    return status
                elif status in ["failed", "stopped"]:
                    progress.update(task, description=f"{description} - ✗ {status.title()}")
                    raise RuntimeError(f"Task {status}")

            except Exception as e:
                if isinstance(e, RuntimeError):
                    raise
                console.print(f"[yellow]Warning:[/yellow] Error checking status: {e}")

            time.sleep(poll_interval)

        raise TimeoutError(f"Task timed out after {timeout} seconds")


def batch_upload_progress(files: list[str]) -> tuple[list[str], list[str]]:
    """Upload multiple files with progress display.

    Args:
        files: List of file paths to upload

    Returns:
        Tuple of (successful_uploads, failed_uploads)
    """
    successful = []
    failed = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Uploading {len(files)} files...", total=len(files))

        for i, file_path in enumerate(files, 1):
            try:
                # This is a placeholder - actual upload logic should be injected
                progress.update(task, description=f"Uploading {file_path}...")
                # upload_file(file_path)  # Actual upload would happen here
                successful.append(file_path)
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to upload {file_path}: {e}")
                failed.append(file_path)

            progress.update(task, advance=1)

    return successful, failed
