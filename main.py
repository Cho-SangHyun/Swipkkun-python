from fastapi import FastAPI
from pydantic import BaseModel
from gpt import user_interact
from database import EngineConn
from models import RentalPost, Member

import pandas as pd
from sentence_transformers import SentenceTransformer, util

app = FastAPI()
engine = EngineConn()
session = engine.sessionmaker()


class Message(BaseModel):
    message: str


@app.post("/api/chat/send-message")
async def reply_message(message: Message):
    rental_post_data = session.query(RentalPost).all()
    machined_data = {
        'rental_post_id': [],
        'product_name': [],
        'description': [],
        'precaution': [],
        'rental_price': []
    }
    for data in rental_post_data:
        machined_data['rental_post_id'].append(data.rental_post_id)
        machined_data['product_name'].append(data.product_name)
        machined_data['description'].append(data.description)
        machined_data['precaution'].append(data.precaution)
        machined_data['rental_price'].append(data.rental_price)

    df = pd.DataFrame(machined_data)
    df['feature'] = df['product_name'] + " / " + df['description'] + " / " + df['precaution']
    
    model = SentenceTransformer("sentence-transformers/distiluse-base-multilingual-cased-v2")

    df['hf_embeddings'] = df['feature'].apply(lambda x : model.encode(x))

    user_message = message.message
    rental_post_id, gpt_reply_message = user_interact(user_message, model, df)

    if rental_post_id == -1:
        return {
            "recommend_success": False,
            "recommend_message": gpt_reply_message 
        }

    recommended_product = session.query(RentalPost).filter(RentalPost.rental_post_id == rental_post_id).first()
    product_owner = session.query(Member).filter(Member.member_id == recommended_product.member_id).first()
    
    return {
        "recommend_success": True,
        "recommend_message": gpt_reply_message,
        "recommend_product" : {
            "rental_post_id": recommended_product.rental_post_id,
            "product_owner": product_owner.nickname,
            "product_name": recommended_product.product_name,
            "description": recommended_product.description,
            "precaution": recommended_product.precaution,
            "rental_price": recommended_product.rental_price
        }
    }


