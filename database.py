import dataclasses
import logging

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


logger = logging.getLogger(__name__)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class GroupUser(Base):
    __tablename__ = "group_users"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE")
    )

    status: Mapped[str] = mapped_column(String(32))

    user: Mapped["User"] = relationship(back_populates="groups")
    group: Mapped["Group"] = relationship(back_populates="users")

    def __repr__(self):
        return (
            f"GroupUsers(user_id={self.user_id}, "
            f"group_id={self.group_id}, status={self.status})"
        )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(unique=True)

    groups: Mapped[list["GroupUser"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"User(id={self.id}, user_id={self.user_id})"


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[str] = mapped_column(unique=True)
    settings: Mapped[JSON] = mapped_column(type_=JSON)

    users: Mapped[list["GroupUser"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"Group(id={self.id}, settings={self.settings})"
