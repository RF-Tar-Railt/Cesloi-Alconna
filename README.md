# Cesloi-Alconna
Cesloi-CommandAnalysis的高级版，支持解析消息链

Alconna表示想变得更~~可爱~~美观一点

## Example
```python
from cesloi.alconna import Alconna, Option, AnyStr

cmd = Alconna(
    headers=["/"],
    command="pip",
    options=[
        Option("install", pak_name=AnyStr),
        Option("list"),
        Option("--upgrade")
    ]
)

msg = "/pip install cesloi"
result = cmd.analysis_message(msg) # 该方法返回一个Arpamar类的实例
print(result.get('install'))
```
其结果为
```
{'pak_name': 'cesloi'}
```
