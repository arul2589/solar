"""Database engine and the mandatory tenant filter.

Every model that inherits `TenantMixin` carries `installer_id`. A Session is bound to one
tenant through `session.info["installer_id"]`. An ORM event adds
`WHERE installer_id = :tenant` to every SELECT/UPDATE/DELETE that touches a tenant table,
and a flush hook stamps/validates `installer_id` on writes. A session with no tenant that
touches a tenant table raises, so forgetting to scope a query fails loudly instead of
leaking data. Only platform-owner code may set `tenant_bypass`.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, create_engine, event
from sqlalchemy.orm import (DeclarativeBase, Mapped, Session, declared_attr, mapped_column, sessionmaker,
                            with_loader_criteria)

from .config import get_config


class TenantError(RuntimeError):
    pass


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TenantMixin:
    @declared_attr
    def installer_id(cls) -> Mapped[int]:  # noqa: N805
        return mapped_column(ForeignKey("installer.id", ondelete="CASCADE"), index=True, nullable=False)


def _make_engine(url: str):
    kw = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kw["connect_args"] = {"check_same_thread": False}
    eng = create_engine(url, **kw)
    if url.startswith("sqlite"):
        @event.listens_for(eng, "connect")
        def _fk_on(dbapi_conn, _):
            dbapi_conn.execute("PRAGMA foreign_keys=ON")
    return eng


engine = _make_engine(get_config().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def rebind(url: str):
    """Used by tests to point the app at a fresh database."""
    global engine
    engine = _make_engine(url)
    SessionLocal.configure(bind=engine)
    return engine


def _touches_tenant_table(state) -> bool:
    for m in state.all_mappers:
        if issubclass(m.class_, TenantMixin):
            return True
    return False


@event.listens_for(Session, "do_orm_execute")
def _tenant_criteria(state):
    if not (state.is_select or state.is_update or state.is_delete):
        return
    if state.execution_options.get("include_all_tenants") or state.session.info.get("tenant_bypass"):
        return
    tid = state.session.info.get("installer_id")
    if tid is None:
        if _touches_tenant_table(state):
            raise TenantError("Query on a tenant table without a tenant-scoped session")
        return
    state.statement = state.statement.options(
        with_loader_criteria(TenantMixin, lambda cls: cls.installer_id == tid, include_aliases=True)
    )


@event.listens_for(Session, "before_flush")
def _tenant_stamp(session, flush_context, instances):
    bypass = session.info.get("tenant_bypass")
    tid = session.info.get("installer_id")
    for obj in session.new:
        if isinstance(obj, TenantMixin):
            if obj.installer_id is None:
                if tid is None:
                    raise TenantError(f"New {type(obj).__name__} has no installer_id and session has no tenant")
                obj.installer_id = tid
            elif not bypass and tid is not None and obj.installer_id != tid:
                raise TenantError("Cannot write a row for another installer")
    for obj in session.dirty:
        if isinstance(obj, TenantMixin) and not bypass:
            if tid is not None and obj.installer_id != tid:
                raise TenantError("Cannot modify a row of another installer")
        if getattr(obj, "__immutable__", False) and session.is_modified(obj):
            raise TenantError(f"{type(obj).__name__} rows are immutable")
    for obj in session.deleted:
        if getattr(obj, "__immutable__", False):
            raise TenantError(f"{type(obj).__name__} rows are immutable")


def tenant_session(installer_id: int | None, *, bypass: bool = False) -> Session:
    s = SessionLocal()
    s.info["installer_id"] = installer_id
    s.info["tenant_bypass"] = bypass
    return s


@contextmanager
def session_scope(installer_id: int | None, *, bypass: bool = False):
    s = tenant_session(installer_id, bypass=bypass)
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
