import re

re.DOTALL = True

def extract_commands(input: str):
    pattern = r'```(?:shell|bash|cmd|exec)\n([\s\S]*?)\n```'
    result = re.findall(pattern, input)
    return result

if __name__ == "__main__":
    input = "```shell\ncd && ls .\n```"
    result = extract_commands(input)
    for cmd in extract_commands(input):
        print(cmd)
    input = "```shell\nls -l\ncd ..\ncd -\n```"
    result = extract_commands(input)
    for cmd in extract_commands(input):
        print(cmd)

    input = """```shell
    echo "MIT License

    Copyright (c) $(date +"%Y") David Laeer

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the \"Software\"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE." > LICENSE
```"""
    result = extract_commands(input)