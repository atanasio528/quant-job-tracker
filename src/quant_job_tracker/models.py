from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    group: Mapped[str]
    career_url: Mapped[str]
    ats: Mapped[str | None] = mapped_column(default=None)
    active: Mapped[bool] = mapped_column(default=True)
    notes: Mapped[str | None] = mapped_column(default=None)

    jobs: Mapped[list["Job"]] = relationship(back_populates="company_ref")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    company: Mapped[str] = mapped_column(index=True)
    title: Mapped[str] = mapped_column(index=True)
    loc: Mapped[str] = mapped_column(index=True)
    url: Mapped[str] = mapped_column(unique=True)
    source: Mapped[str]
    jd: Mapped[str]
    jd_hash: Mapped[str] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(default="new", index=True)
    first_seen: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    last_seen: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(default=None)
    crawl_note: Mapped[str | None] = mapped_column(default=None)

    company_ref: Mapped[Company] = relationship(back_populates="jobs")
    evals: Mapped[list["Eval"]] = relationship(back_populates="job")


class Eval(Base):
    __tablename__ = "evals"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    front: Mapped[str] = mapped_column(index=True)
    h1b: Mapped[str] = mapped_column(index=True)
    exp: Mapped[str] = mapped_column(index=True)
    score: Mapped[int] = mapped_column(index=True)
    reason: Mapped[str]
    flags: Mapped[str] = mapped_column(default="")
    model: Mapped[str]
    policy_ver: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    job: Mapped[Job] = relationship(back_populates="evals")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    decision: Mapped[str] = mapped_column(index=True)
    note: Mapped[str | None] = mapped_column(default=None)
    reviewer: Mapped[str] = mapped_column(default="user")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class App(Base):
    __tablename__ = "apps"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), unique=True, index=True)
    app_status: Mapped[str] = mapped_column(default="not_started", index=True)
    deadline: Mapped[str | None] = mapped_column(String(40), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(40), nullable=True)
    applied_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    contact: Mapped[str | None] = mapped_column(default=None)
    note: Mapped[str | None] = mapped_column(default=None)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(index=True)
    jobs_found: Mapped[int] = mapped_column(default=0)
    jobs_stored: Mapped[int] = mapped_column(default=0)
    jobs_evaluated: Mapped[int] = mapped_column(default=0)
    error: Mapped[str | None] = mapped_column(default=None)
    policy_ver: Mapped[str] = mapped_column(default="v1")
    model: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
