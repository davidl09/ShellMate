from .thinkinganimation import ThinkingAnimation

anim = ThinkingAnimation()

def remove_think_block(raw: str) -> str:
    if not ("<think>" in raw and "</think>" in raw):
        return raw
    
    endthink = raw.find("</think>")
    return raw[endthink + len("</think>"):]
        

def handle_response(stream, printAll = False) -> str:
    thinking = False
    endthink_seq = False
    raw_response = ""

    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            chunk = chunk.choices[0].delta.content
            raw_response += chunk
            if printAll:
                print(chunk, end="", flush=True)

            if (len(raw_response) > 0 and raw_response in "<think>") or "<think>" in raw_response:
                thinking = True
            if "</think>" in raw_response:
                thinking = False
                if not endthink_seq:
                    endthink = raw_response.find("</think>") + len("</think>")
                    chunk = raw_response[endthink:]
                    endthink_seq = True

            if thinking and not printAll:
                anim.start()
            else:
                anim.stop()
                if not printAll:
                    print(chunk, end="", flush=True)
    
    print("")
    return remove_think_block(raw_response)


'<think>\nTo find out what day it is, I need to run the `date` command, which will provide the current date and time, including the day of the week. I will execute this command to get the information.\n</think>\n'
