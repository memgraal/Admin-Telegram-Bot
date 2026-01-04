import logging
from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


logger = logging.getLogger(__name__)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class GroupUsers(Base):
    __tablename__ = "group_users"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE")
    )

    status: Mapped[str] = mapped_column(String(32))

    user: Mapped["Users"] = relationship(back_populates="groups")
    group: Mapped["Groups"] = relationship(back_populates="users")

    def __repr__(self):
        return (
            f"GroupUsers(user_id={self.user_id}, "
            f"group_id={self.group_id}, status={self.status})"
        )


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(unique=True)

    groups: Mapped[list["GroupUsers"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"User(id={self.id}, user_id={self.user_id})"


class Groups(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    settings: Mapped[JSON] = mapped_column(type_=JSON)

    users: Mapped[list["GroupUsers"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"Group(id={self.id}, settings={self.settings})"
