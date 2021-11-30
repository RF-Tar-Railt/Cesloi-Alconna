import time

from arclet.cesloi.message.alconna import Alconna, Option
from arclet.cesloi.message.element import At
from arclet.cesloi.message.messageChain import MessageChain

ping = Alconna(
        headers=["."],
        command="test",
        options=[
            Option('--foo', bar=At)
        ]
    )

msg = MessageChain.create(".test", " --foo", At(123))
print(ping.analysis_message(msg).matched)
count = 20000
start =time.time()
test_stack = [0]
for i in range(count):
    if ping.analysis_message(msg).matched:
        test_stack[0] += 1
end = time.time()
print(f"{test_stack[0] / (end-start):.2f}msg/s")