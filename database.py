from sqlalchemy import ForeignKey, JSON, String, DateTime, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(unique=True)

    groups: Mapped[list["GroupUser"]] = relationship(
        back_populates="user",
        cascade="all"
    )


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[str] = mapped_column(unique=True)

    settings: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=dict
    )

    users: Mapped[list["GroupUser"]] = relationship(
        back_populates="group",
        cascade="all"
    )


class Logs(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    chat_id: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    action: Mapped[str] = mapped_column(String(64))

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
