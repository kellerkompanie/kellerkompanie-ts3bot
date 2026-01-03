from datetime import datetime

from sqlalchemy import String, Text, DateTime, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TeamspeakMessage(Base):
    __tablename__ = "teamspeak_messages"

    message_type: Mapped[str] = mapped_column(String(50), primary_key=True)
    message_text: Mapped[str] = mapped_column(Text)


class TeamspeakAccount(Base):
    __tablename__ = "teamspeak_accounts"

    teamspeak_uid: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger)
    steam_id: Mapped[str | None] = mapped_column(String(255))


class TeamspeakAuthkey(Base):
    __tablename__ = "teamspeak_authkeys"

    authkey: Mapped[str] = mapped_column(String(32), primary_key=True)
    teamspeak_uid: Mapped[str] = mapped_column(String(255))
    generated_date: Mapped[datetime] = mapped_column(DateTime)


class SquadXmlEntry(Base):
    __tablename__ = "squad_xml_entries"

    player_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    nick: Mapped[str] = mapped_column(String(255))
