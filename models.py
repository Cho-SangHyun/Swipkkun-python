from sqlalchemy import Column, INT, VARCHAR, DATETIME, Enum ,TEXT, SMALLINT
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

    product_idx = Column(INT, nullable=False, autoincrement=True, primary_key=True)
    member_id = Column(INT, nullable=False)
    product_name = Column(VARCHAR(45), nullable=False)
    product_content = Column(TEXT, nullable=False)
    precaution = Column(TEXT, nullable=False)
    product_price = Column(INT, nullable=False)
    hit_cnt = Column(INT, nullable=False)
    product_img = Column(TEXT, nullable=False)
    product_address = Column(TEXT, nullable=False)
    product_hash_tag = Column(TEXT, nullable=False)
    product_status = Column(INT, nullable=False)
    created_date = Column(DATETIME, nullable=False)
    updated_date = Column(DATETIME, nullable=False)