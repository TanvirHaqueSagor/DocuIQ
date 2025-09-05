import os, json, sqlite3, math
from typing import Iterable, List, Dict, Any


def _ensure_db(conn: sqlite3.Connection):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            metadata TEXT,
            embedding TEXT NOT NULL -- JSON array of floats
        )
        """
    )
    conn.commit()


def _norm(v: List[float]) -> float:
    return math.sqrt(sum(x * x for x in v)) or 1.0


def _cosine(a: List[float], b: List[float]) -> float:
    # assume same length
    dot = sum(x * y for x, y in zip(a, b))
    na = _norm(a)
    nb = _norm(b)
    return dot / (na * nb)


class VectorStore:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        _ensure_db(self.conn)

    def add_many(self, items: Iterable[Dict[str, Any]]):
        rows = []
        for it in items:
            rows.append(
                (
                    it["id"],
                    it.get("content") or "",
                    json.dumps(it.get("metadata") or {}),
                    json.dumps(list(map(float, it.get("embedding") or []))),
                )
            )
        with self.conn:
            self.conn.executemany("INSERT OR REPLACE INTO items (id, content, metadata, embedding) VALUES (?,?,?,?)", rows)

    def query(self, embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        # naive: load all vectors and score in python
        cur = self.conn.cursor()
        cur.execute("SELECT id, content, metadata, embedding FROM items")
        scored = []
        for _id, content, meta_json, emb_json in cur.fetchall():
            try:
                emb = json.loads(emb_json)
            except Exception:
                continue
            score = _cosine(embedding, emb)
            m = {}
            try:
                m = json.loads(meta_json or "{}")
            except Exception:
                m = {}
            scored.append({"id": _id, "content": content, "metadata": m, "score": float(score)})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[: top_k or 5]

    def delete_by_document_id(self, document_id: str) -> int:
        """Delete all items whose metadata.document_id matches.
        Returns number of rows deleted.
        """
        cur = self.conn.cursor()
        cur.execute("SELECT id, metadata FROM items")
        ids = []
        for _id, meta_json in cur.fetchall():
            try:
                m = json.loads(meta_json or "{}")
            except Exception:
                m = {}
            if str(m.get('document_id')) == str(document_id):
                ids.append(_id)
        if not ids:
            return 0
        with self.conn:
            cur.executemany("DELETE FROM items WHERE id = ?", [(i,) for i in ids])
        return len(ids)


def chunk_text(text: str, target_chars: int = 1200, overlap: int = 120) -> Iterable[str]:
    text = text or ""
    n = max(200, target_chars)
    o = max(0, min(overlap, n // 3))
    i = 0
    L = len(text)
    while i < L:
        j = min(L, i + n)
        yield text[i:j]
        if j >= L:
            break
        i = j - o
