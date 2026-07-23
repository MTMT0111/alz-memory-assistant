"""基于 ChromaDB 的长期记忆语义检索服务。

本模块只维护独立向量库，不修改 SQLite 表结构，也不接入现有 chat_service 主链路。
"""

from __future__ import annotations

import asyncio
from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import sqlite3
from typing import Any
from urllib import error, request

from app.config import load_local_env_file


load_local_env_file()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHROMA_DIR = BASE_DIR / "data" / "chroma"
COLLECTION_NAME = "approved_memories"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_TIMEOUT_SECONDS = 8
MEMORY_CATEGORIES = ("家人", "往事", "爱好", "其他")

_client: Any | None = None
_collection: Any | None = None
_embedding_model: Any | None = None
_init_lock: asyncio.Lock | None = None
_last_sync_count = 0


def _env_value(name: str) -> str:
    """读取环境变量，并把示例占位符视为未配置。"""
    value = os.getenv(name, "").strip()
    if not value or "your_" in value.lower() or "_here" in value.lower():
        return ""
    return value


def _normalize_category(value: Any) -> str:
    """将历史分类归一到追忆页固定的四类。"""
    text = str(value or "").strip()
    if text in MEMORY_CATEGORIES:
        return text
    lowered = text.lower()
    if any(keyword in text for keyword in ("家", "儿", "女", "孙", "伴侣", "丈夫", "妻子", "亲人", "妈妈", "爸爸")):
        return "家人"
    if any(keyword in text for keyword in ("爱好", "喜欢", "音乐", "唱歌", "跳舞", "园艺", "做饭", "兴趣")):
        return "爱好"
    if any(keyword in text for keyword in ("往事", "过去", "年轻", "工作", "学校", "故乡", "老家", "经历", "old_event", "old_place")):
        return "往事"
    if lowered in {"family", "family_photo", "person", "people"}:
        return "家人"
    if lowered in {"hobby", "familiar_music", "daily_object"}:
        return "爱好"
    if lowered in {"memory", "event", "place", "old_event", "old_place", "life_story"}:
        return "往事"
    return "其他"


def _classify_memory_category(text: str) -> str:
    """用 DeepSeek 给缺失分类的记忆打标签；失败时默认归入“其他”。"""
    api_key = _env_value("DEEPSEEK_API_KEY")
    clean_text = str(text or "").strip()
    if not api_key or not clean_text:
        return "其他"

    prompt = (
        "请将以下记忆文本分类为：家人、往事、爱好、其他 之一。\n"
        "只输出分类名称，不输出其他内容。\n"
        f"记忆文本：{clean_text[:500]}"
    )
    payload = {
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip() or "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 20,
    }
    api_request = request.Request(
        url=DEEPSEEK_CHAT_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(api_request, timeout=DEEPSEEK_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
        category = str(data["choices"][0]["message"]["content"] or "").strip()
        return _normalize_category(category)
    except (error.HTTPError, KeyError, IndexError, json.JSONDecodeError, Exception):
        return "其他"


def _get_init_lock() -> asyncio.Lock:
    """懒创建初始化锁，避免并发请求同时加载 Chroma 和 embedding 模型。"""
    global _init_lock
    if _init_lock is None:
        _init_lock = asyncio.Lock()
    return _init_lock


def _load_dependencies() -> tuple[Any, Any]:
    """懒加载重依赖，避免未安装向量依赖时影响普通 Web 服务启动。"""
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
    except Exception as exc:  # pragma: no cover - 依赖由部署环境决定
        raise RuntimeError(
            "缺少语义检索依赖，请先执行：pip install chromadb sentence-transformers"
        ) from exc
    return chromadb, SentenceTransformer


def _get_embedding_model() -> Any:
    """加载并复用多语言 embedding 模型，支持中文语义检索。"""
    global _embedding_model
    if _embedding_model is None:
        _, sentence_transformer = _load_dependencies()
        _embedding_model = sentence_transformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def _embed_texts(texts: list[str]) -> list[list[float]]:
    """将文本转成向量；Chroma upsert/query 都复用这一套 embedding。"""
    model = _get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return [list(map(float, item)) for item in embeddings]


def _get_collection() -> Any:
    """创建 persistent Chroma collection，数据落盘到 data/chroma/。"""
    global _client, _collection
    if _collection is None:
        chromadb, _ = _load_dependencies()
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "已审批长期记忆语义索引"},
        )
    return _collection


async def _ensure_initialized() -> None:
    """首次检索/写入时才初始化向量库和模型，避免应用启动变慢。"""
    global _embedding_model
    if _collection is not None and _embedding_model is not None:
        return

    async with _get_init_lock():
        if _collection is None:
            _get_collection()
        if _embedding_model is None:
            _, sentence_transformer = _load_dependencies()
            _embedding_model = sentence_transformer(EMBEDDING_MODEL_NAME)


def _clean_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
    """Chroma metadata 只接受简单类型，这里做一次安全归一化。"""
    cleaned: dict[str, str | int | float | bool] = {}
    for key, value in dict(metadata or {}).items():
        if isinstance(value, (str, int, float, bool)):
            cleaned[str(key)] = value
        elif value is not None:
            cleaned[str(key)] = str(value)
    cleaned.setdefault("patient_id", "")
    cleaned.setdefault("category", "其他")
    cleaned.setdefault("approved", True)
    cleaned["patient_id"] = str(cleaned.get("patient_id") or "")
    cleaned["category"] = _normalize_category(cleaned.get("category"))
    cleaned["approved"] = bool(cleaned.get("approved", True))
    return cleaned


async def upsert_memory(memory_id: str, text: str, metadata: dict) -> None:
    """将一条已审批记忆写入向量库；相同 memory_id 重复写入会覆盖更新。"""
    clean_id = str(memory_id or "").strip()
    clean_text = str(text or "").strip()
    if not clean_id or not clean_text:
        return

    normalized_metadata = _clean_metadata(metadata)
    normalized_metadata["approved"] = bool(normalized_metadata.get("approved", True))
    await _ensure_initialized()
    collection = _get_collection()
    collection.upsert(
        ids=[clean_id],
        documents=[clean_text],
        embeddings=_embed_texts([clean_text]),
        metadatas=[normalized_metadata],
    )


async def search_memory(query: str, patient_id: str, top_k: int = 4) -> list[dict]:
    """按 query 检索某位患者最相关的 top_k 条已审批记忆。"""
    clean_query = str(query or "").strip()
    clean_patient_id = str(patient_id or "").strip()
    if not clean_query or not clean_patient_id:
        return []

    await _ensure_initialized()
    collection = _get_collection()
    limit = max(1, min(int(top_k or 4), 20))
    result = collection.query(
        query_embeddings=_embed_texts([clean_query]),
        n_results=limit,
        where={
            "$and": [
                {"patient_id": {"$eq": clean_patient_id}},
                {"approved": {"$eq": True}},
            ]
        },
        include=["documents", "distances", "metadatas"],
    )

    ids = (result.get("ids") or [[]])[0]
    documents = (result.get("documents") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    memories: list[dict] = []
    for index, memory_id in enumerate(ids):
        distance = float(distances[index]) if index < len(distances) else 0.0
        # Chroma 距离越小越相关，转成 0-1 附近的正向分数，方便前端/调试查看。
        score = 1.0 / (1.0 + max(distance, 0.0))
        memories.append(
            {
                "memory_id": str(memory_id),
                "text": str(documents[index] if index < len(documents) else ""),
                "score": round(score, 6),
            }
        )
    return memories


async def get_memories_by_category(patient_id: str) -> dict[str, list[dict]]:
    """返回某位患者已审批记忆，按追忆页四类分组。"""
    clean_patient_id = str(patient_id or "").strip()
    grouped: dict[str, list[dict]] = {category: [] for category in MEMORY_CATEGORIES}
    if not clean_patient_id:
        return grouped

    await _ensure_initialized()
    collection = _get_collection()
    result = collection.get(
        where={
            "$and": [
                {"patient_id": {"$eq": clean_patient_id}},
                {"approved": {"$eq": True}},
            ]
        },
        include=["documents", "metadatas"],
    )

    ids = result.get("ids") or []
    documents = result.get("documents") or []
    metadatas = result.get("metadatas") or []
    for index, memory_id in enumerate(ids):
        metadata = dict(metadatas[index] or {}) if index < len(metadatas) else {}
        category = _normalize_category(metadata.get("category"))
        memory = {
            "memory_id": str(memory_id),
            "text": str(documents[index] if index < len(documents) else ""),
            "category": category,
            "approved_at": metadata.get("approved_at") or metadata.get("updated_at") or metadata.get("created_at") or "",
            "source": metadata.get("source") or metadata.get("source_message") or metadata.get("conversation_id") or "",
            "metadata": metadata,
        }
        grouped.setdefault(category, []).append(memory)

    for category in MEMORY_CATEGORIES:
        grouped[category] = sorted(
            grouped.get(category, []),
            key=lambda item: str(item.get("approved_at") or ""),
            reverse=True,
        )
    return grouped


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    """检查 SQLite 中是否存在目标表，不存在时同步任务安全跳过。"""
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return bool(row)


def _column_names(connection: sqlite3.Connection, table_name: str) -> set[str]:
    """读取表字段，用于兼容不同历史版本的 approved_memories 表。"""
    return {str(row["name"]) for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()}


def _first_existing(columns: set[str], candidates: tuple[str, ...]) -> str | None:
    """从候选字段名里挑一个当前表真实存在的字段。"""
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _row_text(row: sqlite3.Row, columns: set[str]) -> str:
    """把一条 SQLite 记忆记录转成可 embedding 的文本。"""
    text_column = _first_existing(columns, ("text", "content", "memory_text", "summary", "description"))
    if text_column:
        return str(row[text_column] or "").strip()

    pieces: list[str] = []
    for column in ("title", "category", "source_message", "suggested_description", "notes"):
        if column in columns and row[column]:
            pieces.append(str(row[column]).strip())
    return "；".join(piece for piece in pieces if piece)


def _row_approved(row: sqlite3.Row, columns: set[str]) -> bool:
    """兼容 approved/status/is_approved 等常见审批字段。"""
    if "approved" in columns:
        return str(row["approved"]).strip().lower() in {"1", "true", "yes", "approved"}
    if "is_approved" in columns:
        return str(row["is_approved"]).strip().lower() in {"1", "true", "yes", "approved"}
    if "status" in columns:
        return str(row["status"] or "").strip().lower() == "approved"
    return True


def _row_metadata_value(row: sqlite3.Row, columns: set[str], candidates: tuple[str, ...]) -> str:
    """从 SQLite 记录中安全读取可选元数据字段。"""
    column = _first_existing(columns, candidates)
    if not column:
        return ""
    return str(row[column] or "").strip()


async def sync_from_sqlite(db_path: str) -> None:
    """从 approved_memories 表幂等同步已审批记忆到 Chroma 向量库。"""
    global _last_sync_count
    _last_sync_count = 0
    database_path = str(db_path or "").strip()
    if not database_path:
        return

    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row
        if not _table_exists(connection, "approved_memories"):
            return

        columns = _column_names(connection, "approved_memories")
        id_column = _first_existing(columns, ("memory_id", "id", "uuid")) or "rowid"
        patient_column = _first_existing(columns, ("patient_id", "user_profile_id", "user_id"))
        category_column = _first_existing(columns, ("category", "memory_type", "type"))

        rows = connection.execute("SELECT rowid, * FROM approved_memories").fetchall()

    for row in rows:
        if not _row_approved(row, columns):
            continue
        text = _row_text(row, columns)
        if not text:
            continue

        raw_id = row[id_column] if id_column in row.keys() else row["rowid"]
        patient_id = str(row[patient_column]) if patient_column else ""
        raw_category = str(row[category_column] or "").strip() if category_column else ""
        category = _normalize_category(raw_category) if raw_category else _classify_memory_category(text)
        await upsert_memory(
            memory_id=str(raw_id),
            text=text,
            metadata={
                "patient_id": patient_id,
                "category": category,
                "approved": True,
                "approved_at": _row_metadata_value(row, columns, ("approved_at", "updated_at", "created_at", "timestamp")),
                "source": _row_metadata_value(row, columns, ("source", "source_message", "conversation_id")),
            },
        )
        _last_sync_count += 1


def get_last_sync_count() -> int:
    """返回最近一次 sync_from_sqlite 成功写入/更新的记录数，供脚本打印。"""
    return _last_sync_count


def get_chroma_entry_count() -> int:
    """返回当前 Chroma 记忆条目数；依赖缺失时安全返回 0。"""
    try:
        collection = _get_collection()
        return int(collection.count())
    except Exception:
        return 0


def clear_chroma_cache() -> None:
    """清空本地 Chroma 缓存，不影响 SQLite 主库。"""
    global _client, _collection, _embedding_model
    _client = None
    _collection = None
    _embedding_model = None
    shutil.rmtree(CHROMA_DIR, ignore_errors=True)
