from __future__ import annotations

from itertools import count
from typing import Dict, List, Optional

from models.user import User

_USERS_BY_ID: Dict[int, User] = {}
_NEXT_ID = count(1)


def list_users() -> List[User]:
    return list(_USERS_BY_ID.values())


def get_user_by_id(user_id: int) -> Optional[User]:
    return _USERS_BY_ID.get(user_id)


def get_user_by_email(email: str) -> Optional[User]:
    normalized = email.strip().lower()
    for user in _USERS_BY_ID.values():
        if user.email.strip().lower() == normalized:
            return user
    return None


def create_user(name: str, email: str) -> User:
    user = User(id=next(_NEXT_ID), name=name.strip(), email=email.strip())
    _USERS_BY_ID[user.id] = user
    return user


def get_or_create_user(name: str, email: str) -> User:
    existing = get_user_by_email(email)
    if existing:
        return existing
    return create_user(name=name, email=email)
