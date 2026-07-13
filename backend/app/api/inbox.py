from fastapi import APIRouter, Depends, HTTPException

from app.main_deps import get_conn

router = APIRouter(prefix="/api/inbox")


@router.get("")
def list_inbox(unread_only: int = 0, limit: int = 200, conn=Depends(get_conn)):
    sql = (
        "SELECT m.id, m.lead_no, m.channel, m.kind, m.from_addr, m.subject, m.body,"
        "       m.received_at, m.is_read, l.company_en, l.country"
        " FROM inbox_messages m JOIN leads l ON l.no = m.lead_no")
    if unread_only:
        sql += " WHERE m.is_read = 0"
    sql += " ORDER BY m.received_at DESC, m.id DESC LIMIT ?"
    return [dict(r) for r in conn.execute(sql, (limit,))]


@router.get("/unread_count")
def unread_count(conn=Depends(get_conn)):
    row = conn.execute("SELECT COUNT(*) c FROM inbox_messages WHERE is_read = 0").fetchone()
    return {"count": row["c"]}


@router.post("/{message_id}/read")
def mark_read(message_id: int, conn=Depends(get_conn)):
    cur = conn.execute("UPDATE inbox_messages SET is_read = 1 WHERE id = ?", (message_id,))
    conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="message not found")
    return {"ok": True}
