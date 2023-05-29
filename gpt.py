from sentence_transformers import SentenceTransformer, util
from starlette.config import Config
import torch
import openai
import json

config = Config(".env")
openai.api_key = config("OPEN_AI_KEY")

database = []
msg_prompt = {
    '추천' : {
                'system' : "당신은 '쉽꾼'이라는 이름의 온라인 렌탈샵에서 사용자의 요구에 맞는 아이템을 추천해주는 어시스턴트입니다", 
                'user' : "'물론이죠!'로 시작하는 간단한 인사말을 1문장 작성한 후 다음 내용을 바탕으로 사용자에게 아이템을 추천합니다. \n context:", 
              },
    '설명' : {
                'system' : "당신은 친절하게 설명해주는 어시스턴트입니다", 
                'user' : "'물론이죠!'로 시작하는 간단한 인사말을 1문장 작성한 후 사용자에게 아이템을 설명합니다", 
              },
    '의도파악' : {
                'system' : "당신은 사용자의 질문의 의도를 파악하는 어시스턴트입니다",
                'user' : "다음 문장은 '설명', '추천', '검색' 중 어느 범주에 속합니까? 범주만 대답합니다. \n context:"
                }         
}

def get_chatgpt_reply(msg):
    completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=msg
                )
    return completion['choices'][0]['message']['content']

def get_query_sim_top_k(query, model, df, top_k):
    query_encode = model.encode(query)
    cos_scores = util.pytorch_cos_sim(query_encode, df['hf_embeddings'].tolist())[0]
    top_results = torch.topk(cos_scores, k=top_k)
    return top_results

# 프롬프트 형태를 만드는 함수
def set_prompt(intent, query, msg_prompt_init, product_info=None):
    m = dict()
    # 검색 또는 추천이면
    if ('추천' in intent) or ('검색' in intent):
        msg = msg_prompt_init['추천'] # 시스템 메세지를 가지고오고
        if product_info:
            msg['user'] += f'제품명: {product_info["product_name"]} \n'
            msg['user'] += f'제품 설명: {product_info["description"]} \n'
            msg['user'] += f'대여 시 유의사항: {product_info["precaution"]} \n'
            msg['user'] += f'하루 대여 가격: {product_info["rental_price"]} \n'
    # 설명문이면
    elif '설명' in intent:
        msg = msg_prompt_init['설명'] # 시스템 메세지를 가지고오고
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
    user_intent = get_user_intent(query, msg_prompt_init)
    print("user_intent : ", user_intent)
    
    # 3-1. 추천 또는 검색이면
    if user_intent in ['추천', '검색']:
        # 기존에 메세지가 있으면 쿼리로 대체
        if len(database) > 0 and database[-1]['role'] == 'assistant' and isinstance(database[-1]['content'], dict):
          query = database[-1]['content']['feature']
        # 유사 아이템 가져오기
        #top_result = get_query_sim_top_k(query, model, movies_metadata, top_k=1 if 'recom' in user_intent else 3) # 추천 개수 설정하려면!
        top_result = get_query_sim_top_k(query, model, df, top_k=1)
        #print("top_result : ", top_result)
        # 검색이면, 자기 자신의 컨텐츠는 제외
        top_index = top_result[1].numpy() if '추천' in user_intent else top_result[1].numpy()[1:]

        rental_post_id = json.loads(df.iloc[top_index, :][['rental_post_id']].to_json(orient="records"))[0]["rental_post_id"]

        product_info = df.iloc[top_index, :][['product_name', 'description', 'precaution', 'rental_price']]
        product_info = json.loads(product_info.to_json(orient="records"))[0]

        intent_data = set_prompt(user_intent, query, msg_prompt_init, product_info)
        recommend_message = get_chatgpt_reply(intent_data).replace("\n", "").strip()
        
        database.append({'role' : 'assistant', 'content' : f"{recommend_message}"})
        return (rental_post_id, recommend_message)
    # 3-2. 설명이면
    elif '설명' in user_intent:
        # 이전 메세지에 따라서 설명을 가져와야 하기 때문에 이전 메세지 컨텐츠를 가져옴
        top_result = get_query_sim_top_k(database[-1]['content'], model, df, top_k=1)
        # feature가 상세 설명이라고 가정하고 해당 컬럼의 값(렌탈아이템)을 가져와 출력
        r_set_d = df.iloc[top_result[1].numpy(), :][['feature']]
        r_set_d = json.loads(r_set_d.to_json(orient="records"))[0]
        #데이터베이스에 상품에 대한 설명(feature)과 역할을 추가해서 이를 기반으로 설명할 수 있도록
        database.append({'role' : 'assistant', 'content' : r_set_d})
        print(f"\n describe : {intent_data_msg} {r_set_d}")