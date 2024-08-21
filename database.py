from datetime import datetime
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

engine = create_async_engine('postgresql+asyncpg://postgres:123@localhost:5432/mydb')
new_session = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()

class Document(Base):
    __tablename__ = 'documents'
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True)
    date: so.Mapped[datetime] = so.mapped_column(sa.TIMESTAMP(timezone=True), index=True, server_default=func.now())

    document_texts: so.Mapped['DocumentText'] = so.relationship('DocumentText', back_populates='document')

class DocumentText(Base):
    __tablename__ = 'documents_text'
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    document_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('documents.id'))
    text: so.Mapped[str] = so.mapped_column(sa.String(1000))

    document: so.Mapped[Document] = so.relationship('Document', back_populates='document_texts')


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def delete_tables():
   async with engine.begin() as conn:
       await conn.run_sync(Base.metadata.drop_all)


