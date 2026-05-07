from sqlalchemy import JSON, Column, VARCHAR, BigInteger, Date, Integer, Text, BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from bot_template.db.base import BaseModel


class User(BaseModel):
    __tablename__ = 'users'

    user_id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=False)

    __table_args__ = {'schema': 'polit'}



class Admin(BaseModel):
    __tablename__ = 'admins'

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)
    user_name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)

    __table_args__ = {'schema': 'polit'}


class Channel(BaseModel):
    __tablename__ = 'channels'

    channel_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True, nullable=False)
    channel_name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    accepting_requests: Mapped[str] = mapped_column(VARCHAR(7), nullable=False)
    
    __table_args__ = {'schema': 'polit'}

class Captcha(BaseModel):
    __tablename__ = 'captcha'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    captcha_text: Mapped[str] = mapped_column(Text, nullable=False)
    captcha_file: Mapped[str] = mapped_column(Text)

    __table_args__ = {'schema': 'polit'}

class News(BaseModel):
    __tablename__ = 'news'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    msg: Mapped[str] = mapped_column(JSON)
    format: Mapped[str] = mapped_column(VARCHAR)

    __table_args__ = {'schema': 'polit'}

