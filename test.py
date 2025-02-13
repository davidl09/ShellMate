from openai import OpenAI
import os
from thinkinganimation import ThinkingAnimation

client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
anim = ThinkingAnimation()


messages = [{"role": "user", "content": "9.11 and 9.8, which is greater?"}]
response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=messages,
    stream=True
)

reasoning_content = ""
content = ""
anim.start()
for chunk in response:
    if chunk.choices[0].delta.reasoning_content != None:
        reasoning_content += chunk.choices[0].delta.reasoning_content
    else:
        anim.stop()
        content += chunk.choices[0].delta.content
        print(chunk.choices[0].delta.content, end="")

messages.append({"role": "assistant", "content": content})
messages.append({'role': 'user', 'content': "How many Rs are there in the word 'strawberry'?"})
