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
result = cmd.analysis_message(msg)
print(result.get('install'))