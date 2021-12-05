# Cesloi-Alconna
Cesloi-CommandAnalysis的高级版，支持解析消息链

Alconna表示想变得更~~可爱~~美观一点

## Example
```python
from cesloi.alconna import Alconna, Option, Subcommand, AnyStr

cmd = Alconna(
    headers=["/"],
    command="pip",
    options=[
        Subcommand("install", Option("--upgrade"), args=AnyStr)
        Option("list"),
    ]
)

msg = "/pip install cesloi"
result = cmd.analysis_message(msg) # 该方法返回一个Arpamar类的实例
print(result.get('install'))
```
其结果为
```
{'args': 'cesloi'}
```

## 用法
通过阅读Alconna的签名可以得知，Alconna支持四大类参数：
 - `headers` : 呼叫该命令的命令头，一般是你的机器人的名字或者符号，与command至少有一个填写. 例如: /, !
 - `command` : 命令名称，你的命令的名字，与headers至少有一个填写
 - `options` : 命令选项，你的命令可选择的所有option,是一个包含Subcommand与Option的列表
 - `main_argument` : 主参数，填入后当且仅当命令中含有该参数时才会成功解析

解析时，先判断命令头(即 headers + command),再判断options与main argument, 这里options与main argument在输入指令时是不分先后的

假设有个Alconna如下:
```python
Alconna(
    headers=["/"],
    command="name",
    options=[
        Subcommand("sub_name",Option("sub-opt", sub_arg="sub_arg"), args=sub_main_arg),
        Option("opt", arg="arg")
        ]
    main_argument="main_argument"
)
```
则它可以解析如下命令:
```
/name sub_name sub-opt sub_arg opt arg main_argument
/name sub_name sub_main_arg opt arg main_argument
/name main_argument opt arg
/name main_argument
```
解析成功的命令的参数会保存在analysis_message方法返回的`Arpamar`实例中
