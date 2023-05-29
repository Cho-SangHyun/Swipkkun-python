from sentence_transformers import SentenceTransformer, util
from starlette.config import Config
import torch
import openai
import json
import copy

config = Config(".env")
openai.api_key = config("OPEN_AI_KEY")

msg_prompt = {
    '추천받기' : {
                'system' : "당신은 '쉽꾼'이라는 이름의 온라인 렌탈샵에서 사용자의 요구에 맞는 아이템을 추천해주는 어시스턴트입니다", 
                'user' : "'물론이죠!'로 시작하는 간단한 인사말을 1문장 작성한 후 다음 내용을 바탕으로 사용자에게 아이템을 추천합니다. \n context:", 
              },
    '의도파악' : {
                'system' : "당신은 '쉽꾼'이란 이름의 온라인 렌탈샵에 근무하며, 물품을 대여하러 온 사용자의 질문의 의도를 파악하는 어시스턴트입니다",
                'user' : "다음 문장의 의도는 '탐색', '추천받기', '검색', '대여 희망' 중 어느 범주에 속합니까? 범주만 대답합니다. 만약 속하는 범주가 없다면 '기타'로 대답합니다 \n context:"
                }         
}

def get_chatgpt_reply(msg):
    while True:
        try:
            completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=msg
                )
            return completion['choices'][0]['message']['content']
        except openai.error.RateLimitError:
            pass
    

def get_query_sim_top_k(query, model, df, top_k):
    query_encode = model.encode(query)
    cos_scores = util.pytorch_cos_sim(query_encode, df['hf_embeddings'].tolist())[0]
    top_results = torch.topk(cos_scores, k=top_k)
    return top_results

# 프롬프트 형태를 만드는 함수
def set_prompt(intent, query, msg_prompt_init, product_info=None):
    m = dict()
    print("의도 in set_prompt :", intent)
    # 검색 또는 추천이면
    if intent in ['추천받기', '검색', '탐색', '대여 희망']:
        msg = msg_prompt_init['추천받기'] # 시스템 메세지를 가지고오고
        if product_info:
            msg['user'] += f'제품명: {product_info["product_name"]} \n'
            msg['user'] += f'제품 설명: {product_info["description"]} \n'
            msg['user'] += f'대여 시 유의사항: {product_info["precaution"]} \n'
            msg['user'] += f'하루 대여 가격: {product_info["rental_price"]} \n'
    # intent 파악
    else:
        msg = msg_prompt_init['의도파악']
        msg['user'] += f' {query} \n A:'
    for k, v in msg.items():
        m['role'], m['content'] = k, v
    return [m]

def get_user_intent(query, msg_prompt_init):
    messages = set_prompt('의도파악', query, msg_prompt_init)
    user_intent = get_chatgpt_reply(messages)
    return user_intent

def user_interact(query, model, df, msg_prompt_init=msg_prompt):
    msg_prompt_cp = copy.deepcopy(msg_prompt_init)
    user_intent = get_user_intent(query, msg_prompt_cp)
    print("user_intent : ", user_intent)
    
    # 3-1. 추천 또는 검색이면
    if user_intent in ['추천받기', '검색', '탐색', '대여 희망']:
        # 유사 아이템 가져오기
        top_result = get_query_sim_top_k(query, model, df, top_k=1)
        top_index = top_result[1].numpy()
        # 추천하는 상품의 id
        rental_post_id = json.loads(df.iloc[top_index, :][['rental_post_id']].to_json(orient="records"))[0]["rental_post_id"]

        product_info = df.iloc[top_index, :][['product_name', 'description', 'precaution', 'rental_price']]
        product_info = json.loads(product_info.to_json(orient="records"))[0]

        intent_data = set_prompt(user_intent, query, msg_prompt_cp, product_info)
        recommend_message = get_chatgpt_reply(intent_data).replace("\n", "").strip()
        return (rental_post_id, recommend_message)
    
    return (-1, "죄송합니다")