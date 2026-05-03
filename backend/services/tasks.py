from ..database import get_connection
from ..models.user import User


def create_task(user_id, title, description="", priority=1):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO tasks (user_id, title, description, priority) VALUES (?, ?, ?, ?)",
        (user_id, title, description, priority),
    )
    conn.commit()
    task = get_task_by_id(cursor.lastrowid)
    conn.close()
    return task


def get_task_by_id(task_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def list_user_tasks(user_id, status=None, page=1, limit=20):
    conn = get_connection()
    offset = (page - 1) * limit
    if status:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE user_id = ? AND status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (user_id, status, limit, offset),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset),
        ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


VALID_TRANSITIONS = {
    "pending": {"in_progress", "cancelled"},
    "in_progress": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


def update_task_status(task_id, status):
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        conn.close()
        raise ValueError("Task not found")
    current = row["status"]
    if current == status:
        conn.close()
        raise ValueError(f"Task is already '{status}'")
    if status not in VALID_TRANSITIONS.get(current, set()):
        conn.close()
        raise ValueError(f"Cannot transition from '{current}' to '{status}'")
    conn.execute(
        "UPDATE tasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (status, task_id),
    )
    conn.commit()
    task = get_task_by_id(task_id)
    conn.close()
    return task


def delete_task(task_id):
    conn = get_connection()
    cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def get_task_stats(user_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT status, COUNT(*) as count FROM tasks WHERE user_id = ? GROUP BY status",
        (user_id,),
    ).fetchall()
    conn.close()
    stats = {"total": 0}
    for row in rows:
        stats[row["status"]] = row["count"]
        stats["total"] += row["count"]
    return stats


def _row_to_dict(row):
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "title": row["title"],
        "description": row["description"],
        "status": row["status"],
        "priority": row["priority"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
