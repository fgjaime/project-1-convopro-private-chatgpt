import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from pymongo import DESCENDING
from pymongo.errors import PyMongoError

from db.mongo import get_collection


def get_conversations_collection():
    conversations = get_collection("conversations")
    try:
        conversations.create_index([("last_interacted", DESCENDING)])
    except PyMongoError:
        pass
    return conversations


# ----- helpers ------
def now_utc():
    return datetime.now(timezone.utc)


def create_new_conversation_id() -> str:
    return str(uuid.uuid4())


# ----- core services -----
def create_new_conversation(
    title: Optional[str] = None,
    role: Optional[str] = None,
    content: Optional[str] = None,
) -> str:
    conversations = get_conversations_collection()
    conv_id = create_new_conversation_id()
    ts = now_utc()
    doc = {
        "_id": conv_id,
        "title": title or "Untitled Conversation",
        "messages": [],
        "last_interacted": ts,
    }
    if role and content:
        doc["messages"].append({"role": role, "content": content, "ts": ts})
    conversations.insert_one(doc)
    return conv_id


def add_message(conv_id: str, role: str, content: str) -> bool:
    conversations = get_conversations_collection()
    ts = now_utc()
    res = conversations.update_one(
        {"_id": conv_id},
        {
            "$push": {"messages": {"role": role, "content": content, "ts": ts}},
            "$set": {"last_interacted": ts},
        },
    )
    return res.matched_count == 1


def get_conversation(conv_id: str) -> Optional[Dict[str, Any]]:
    conversations = get_conversations_collection()
    ts = now_utc()
    doc = conversations.find_one_and_update(
        {"_id": conv_id},
        {"$set": {"last_interacted": ts}},
        return_document=True,
    )
    return doc


def get_all_conversations() -> Dict[str, str]:
    conversations = get_conversations_collection()
    cursor = conversations.find({}, {"title": 1}).sort("last_interacted", DESCENDING)
    return {doc["_id"]: doc["title"] for doc in cursor}


# --- Example usage ---

# For a new conversation (with the first message):
# conv_id = create_new_conversation(title="Intro to Deep Learning", role="user", content="What is DL?")
# add_message(conv_id, "assistant", "Answer for DL query")
# print(get_conversation(conv_id))
# print(get_all_conversations())
#
# # For an existing conversation:
# add_message(conv_id, "user", "What is ML?")
# add_message(conv_id, "assistant", "Answer for ML query")
# print(get_conversation(conv_id))
# print(get_all_conversations())
#
# # # For a new conversation (with a different title and first message):
# conv_id2 = create_new_conversation(title="Intro to Generative AI", role="user", content="What is Generative AI?")
# add_message(conv_id2, "assistant", "Answer for Generative AI query")
# print(get_conversation(conv_id2))
# print(get_all_conversations())
