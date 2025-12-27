from backend.db.conn import get_conn


def fetch_admin_logs(
    limit: int = 50,
    action: str | None = None,
    admin_id: str | None = None,
    since: str | None = None
):
    con = get_conn()
    cur = con.cursor()

    where = []
    params = []

    if action:
        where.append("action = ?")
        params.append(action)
    if admin_id:
        where.append("admin_id = ?")
        params.append(admin_id)
    if since:
        where.append("created_at >= ?")
        params.append(since)

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    sql = f"""
        SELECT id, admin_id, action, detail, created_at
        FROM admin_logs
        {where_sql}
        ORDER BY created_at DESC
        LIMIT ?
    """
    params.append(limit)

    rows = cur.execute(sql, params).fetchall()
    con.close()

    return [
        {
            "id": r[0],
            "admin_id": r[1],
            "action": r[2],
            "detail": r[3],
            "created_at": r[4],
        }
        for r in rows
    ]
