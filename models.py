from datetime import datetime
from passlib.hash import bcrypt
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from ext import db


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)

    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary="user_roles", back_populates="users"
    )

    def set_password(self, p: str): self.password_hash = bcrypt.hash(p)

    def check_password(self, p: str) -> bool: return bcrypt.verify(p, self.password_hash)

    def has_role(self, name: str) -> bool: return any(r.name == name for r in self.roles)


class Role(db.Model):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)  # 'admin'/'user'
    desc: Mapped[str | None] = mapped_column(String(255))
    users: Mapped[list[User]] = relationship(
        "User", secondary="user_roles", back_populates="roles"
    )


class UserRole(db.Model):
    __tablename__ = "user_roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "role_id"),)


class ResetToken(db.Model):
    __tablename__ = "reset_tokens"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LoginLog(db.Model):
    __tablename__ = "login_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    login_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(16))  # 'success'/'fail'
    ip: Mapped[str | None] = mapped_column(String(45))
    ua: Mapped[str | None] = mapped_column(String(255))
