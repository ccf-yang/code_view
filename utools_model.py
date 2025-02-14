import base64
import requests
import json

headers = {
    'Host': 'ai.u-tools.cn',
    'accept-language': 'zh-CN',
    'content-type': 'application/json',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) uTools/6.0.1 Chrome/108.0.5359.215 Electron/22.3.27 Safari/537.36',
    'accept': 'text/event-stream',
    'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"'
    }



model_key_map={
    # 每次更改这里后面的模型名字即可，不要更改前面的模型名字，前面名字前端在用
    "deepseek":"deepseek-v3",
    "doubao":"doubao-pro-32k",
    "wenxinspeed":"ERNIE-Speed-128K",
    "wenxin35":"ERNIE-3.5-8K",
    "glm4":"glm-4-flash",
    "deepseekr1":"deepseek-r1",
    "qwen":"qwen-long"
}


def do_request(modelname="deepseek",prompt=""):
    access_token=''
    url = f"https://ai.u-tools.cn/v1/chat/completions?access_token={access_token}&avatar=https%3A%2F%2Fres.u-tools.cn%2Fassets%2Favatars%2Favatar.png"
    payload = json.dumps({
    "model": model_key_map.get(modelname),
    "messages": [
        {
        "role": "system",
        "content": "You are a benevolent programming expert, adept at deciphering code from the perspective of a beginner. The emphasis is on elucidating the functionality and operational mechanisms of the code in accessible and understandable language. Please start by summarizing the overall function of the code, then provide functional annotations for the provided code to help beginners quickly grasp the project and get started. For each function, it is imperative to elucidate its purpose, detailing what it takes as input, what it outputs, and the specific functionality it accomplishes.The explanations should be given in Chinese."
        },
        {
        "role": "user",
        "content": prompt
        }
    ],
    "stream": False
    })
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        res=json.loads(response.text)
        print(res)
        return res.get("choices")[0].get("message").get("content")
    except Exception as e:
        print(e)
        return "error:"+str(e)






if __name__ == "__main__":  
    print(model_key_map.keys())
    model_list=["deepseek","doubao","wenxinspeed","glm4","deepseekr1","qwen","wenxin35"]
    for model in model_list:
        print(f"model:{model}")
        do_request(modelname=model,prompt="hi")
        # break
