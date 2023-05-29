from sqlalchemy import Column, INT, VARCHAR, DATETIME, Enum ,TEXT
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Member(Base):
    __tablename__ = "member"

    member_id = Column(INT, nullable=False, autoincrement=True, primary_key=True)
    email = Column(VARCHAR(255), nullable=False, unique=True)
    password = Column(VARCHAR(60), nullable=False)
    nickname = Column(VARCHAR(10), nullable=False, unique=True)
    phone = Column(VARCHAR(45), nullable=False)
    role = Column(Enum('USER', 'ADMIN'), nullable=False)
    created_date = Column(DATETIME, nullable=False)
    updated_date = Column(DATETIME, nullable=False)

class RentalPost(Base):
    __tablename__ = "rental_post"

    rental_post_id = Column(INT, nullable=False, autoincrement=True, primary_key=True)
    member_id = Column(INT, nullable=False)
    emd_areas_id = Column(INT, nullable=False)
    product_name = Column(VARCHAR(45), nullable=False)
    description = Column(TEXT, nullable=False)
    precaution = Column(TEXT, nullable=False)
    rental_price = Column(INT, nullable=False)
    views = Column(INT, nullable=False)
    created_date = Column(DATETIME, nullable=False)
    updated_date = Column(DATETIME, nullable=False)