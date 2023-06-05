from fastapi import FastAPI
from pydantic import BaseModel
from gpt import user_interact
from database import EngineConn
from models import RentalPost, Member
from fastapi.middleware.cors import CORSMiddleware

import pandas as pd
from sentence_transformers import SentenceTransformer, util

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
engine = EngineConn()
session = engine.sessionmaker()


class Message(BaseModel):
    message: str


@app.post("/test")
async def test_message():
    data = session.query(Member).first()
    return {"message": data.email}

@app.post("/api/chat/send-message")
async def reply_message(message: Message):
    rental_post_data = session.query(RentalPost).all()
    machined_data = {
        'product_idx': [],
        'product_name': [],
        'product_content': [],
        'precaution': [],
        'product_price': [],
        'product_hash_tag': [],
    }
    for data in rental_post_data:
        machined_data['product_idx'].append(data.product_idx)
        machined_data['product_name'].append(data.product_name)
        machined_data['product_content'].append(data.product_content)
        machined_data['precaution'].append(data.precaution)
        machined_data['product_price'].append(data.product_price)
        machined_data['product_hash_tag'].append(data.product_hash_tag.replace("#", ""))

    df = pd.DataFrame(machined_data)
    df['feature'] = df['product_name'] + " / " + df['product_content'] + " / " + df['precaution'] + " / " + df['product_hash_tag']
    
    model = SentenceTransformer("sentence-transformers/distiluse-base-multilingual-cased-v2")

    df['hf_embeddings'] = df['feature'].apply(lambda x : model.encode(x))

    user_message = message.message
    product_idx, gpt_reply_message = user_interact(user_message, model, df)
    
    if product_idx == -1:
        return {
            "recommend_success": False,
            "recommend_message": gpt_reply_message 
        }

    recommended_product = session.query(RentalPost).filter(RentalPost.product_idx == product_idx).first()
    product_owner = session.query(Member).filter(Member.member_id == recommended_product.member_id).first()
    
    return {
        "recommend_success": True,
        "recommend_message": gpt_reply_message,
        "recommend_product" : {
            "product_idx": recommended_product.product_idx,
            "product_owner": product_owner.nickname,
            "product_name": recommended_product.product_name,
            "product_content": recommended_product.product_content,
            "precaution": recommended_product.precaution,
            "product_price": recommended_product.product_price,
            "product_hash_tag": recommended_product.product_hash_tag,
            "product_img": recommended_product.product_img
        }
    }


