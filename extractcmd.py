import re

re.DOTALL = True

def extract_commands(input: str):
    pattern = r'```(?:shell|bash|cmd|exec)\n([\s\S]*?)\n```'
    result = re.findall(pattern, input)
    return [item for sublist in list(map(lambda x: x.split("\n"), result)) for item in sublist]

if __name__ == "__main__":
    input = "```shell\ncd && ls .\n```"
    result = extract_commands(input)
    for cmd in extract_commands(input):
        print(cmd)
    input = "```shell\nls -l\ncd ..\ncd -\n```"
    result = extract_commands(input)
    for cmd in extract_commands(input):
        print(cmd)