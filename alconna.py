from typing import Dict, List, Optional, Union, Type, Any
from pydantic import BaseModel
import re

from arclet.cesloi.message.element import MessageElement
from arclet.cesloi.message.messageChain import MessageChain
from arclet.cesloi.message.utils import split_once
from arclet.cesloi.exceptions import ParamsUnmatched
from arclet.letoderea.entities.decorator import EventDecorator
from arclet.letoderea.utils import ArgumentPackage

AnyIP = r"(\d+)\.(\d+)\.(\d+)\.(\d+)"
AnyDigit = r"(\d+)"
AnyStr = r"(.+)"
AnyUrl = r"(http[s]?://.+)"
Argument_T = Union[str, Type[MessageElement]]


class CommandInterface(BaseModel):
    name: str
    separator: str = " "

    def separate(self, sep: str):
        self.separator = sep
        return self

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"


class OptionInterface(CommandInterface):
    type: str
    args: Dict[str, Argument_T]


class Option(OptionInterface):
    type: str = "OPT"
    args: Dict[str, Argument_T]

    def __init__(self, name: str, **kwargs):
        if name == "":
            raise ValueError("You can't give this with a null name !")
        super().__init__(
            name=name,
            args={k: v for k, v in kwargs.items() if k not in ('name', 'type')}
        )


class Subcommand(OptionInterface):
    type: str = "SBC"
    Options: List[Option]
    args: Dict[str, Argument_T]

    def __init__(self, name: str, *options: Option, **kwargs):
        if name == "":
            raise ValueError("You can't give this with a null name !")
        super().__init__(
            name=name,
            Options=list(options),
            args={k: v for k, v in kwargs.items() if k not in ('name', 'type')}
        )


Options_T = List[OptionInterface]
_builtin_option = Option("-help")


class Arpamar(BaseModel):
    """
    亚帕玛尔(Arpamar), Alconna的珍藏宝书

    Example:
        1.`Arpamar.main_argument`: 当 Alconna 写入了 main_argument 时,该参数返回对应的解析出来的值

        2.`Arpamar.header`: 当 Alconna 的 command 内写有正则表达式时,该参数返回对应的匹配值

        3.`Arpamar.has`: 判断 Arpamar 内是否有对应的属性

        4.`Arpamar.get`: 返回 Arpamar 中指定的属性

        5.`Arpamar.matched`: 返回命令是否匹配成功

    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_index: int = 0  # 记录解析时当前字符串的index
        self.is_str: bool = False  # 是否解析的是string
        self.results: Dict[str, Any] = {'options': {}}
        self.elements: Dict[int, MessageElement] = {}
        self.raw_texts: List[List[Union[int, str]]] = []
        self.need_marg: bool = False
        self.matched: bool = False
        self.head_matched: bool = False
        self._args: Dict[str, Any] = {}

    @property
    def main_argument(self):
        if 'main_argument' in self.results and self.need_marg:
            return self.results['main_argument']

    @property
    def header(self):
        if 'header' in self.results:
            return self.results['header']
        else:
            return self.head_matched

    @property
    def option_args(self):
        return self._args

    def encapsulate_result(self) -> None:
        for k, v in self.results['options'].items():
            k: str = re.sub(r'[\-`~?/.,<>;\':\"|!@#$%^&*()_+=\[\]}{]+', "", k)
            self.__setattr__(k, v)
            if isinstance(v, dict):
                for kk, vv in v.items():
                    if not isinstance(vv, dict):
                        self._args[re.sub(r'[\-`~?/.,<>;\':\"|!@#$%^&*()_+=\[\]}{]+', "", kk)] = vv
                    else:
                        self._args.update(vv)

    def get(self, name: str) -> dict:
        return self.__getattribute__(name)

    def has(self, name: str) -> bool:
        return name in self.__dict__

    def split_by(self, separate: str):
        _text: str = ""  # 重置
        _rest_text: str = ""

        if self.raw_texts[self.current_index][0]:  # 如果命令头匹配后还有字符串没匹配到
            _text, _rest_text = split_once(self.raw_texts[self.current_index][0], separate)

        elif not self.is_str and len(self.raw_texts) > 1:  # 如果命令头匹配后字符串为空则有两种可能，这里选择不止一段字符串
            self.current_index += 1
            _text, _rest_text = split_once(self.raw_texts[self.current_index][0], separate)

        return _text, _rest_text

    class Config:
        extra = 'allow'


class Alconna(CommandInterface):
    """
    亚尔康娜（Alconna），Cesloi的妹妹

    用于更加奇怪(大雾)精确的命令解析，支持String与MessageChain

    样例：Alconna(
        headers=[""],
        command="name",
        options=[
            Subcommand("sub_name",Option("sub-opt", sub_arg=sub_arg), args=sub_main_arg),
            Option("opt", arg=arg)
            ]
        main_argument=main_argument
        )

    其中
        - name: 命令名称
        - sub_name: 子命令名称
        - sub-opt: 子命令选项名称
        - sub_arg: 子命令选项参数
        - sub_main_arg: 子命令主参数
        - opt: 命令选项名称
        - arg: 命令选项参数

    Args:
        headers: 呼叫该命令的命令头，一般是你的机器人的名字或者符号，与 command 至少有一个填写
        command: 命令名称，你的命令的名字，与 headers 至少有一个填写
        options: 命令选项，你的命令可选择的所有 option ，包括子命令与单独的选项
        main_argument: 主参数，填入后当且仅当命令中含有该参数时才会成功解析
    """

    name = "Alconna"
    headers: List[str]
    command: str
    options: Options_T
    main_argument: Argument_T

    def __init__(
            self,
            headers: Optional[List[str]] = None,
            command: Optional[str] = None,
            separator: Optional[str] = None,
            options: Optional[Options_T] = None,
            main_argument: Optional[Argument_T] = None
    ):
        # headers与command二者必须有其一
        if all([all([not headers, not command]), not options, not main_argument]):
            raise ValueError("You must input one parameter!")
        super().__init__(
            headers=headers or [""],
            command=command or "",
            separator=separator or " ",
            options=options or [],
            main_argument=main_argument or "",
        )
        self.options.append(_builtin_option)

        # params是除开命令头的剩下部分
        self._params: Dict[str, Union[Argument_T, Dict[str, Any]]] = {"main_argument": self.main_argument}
        for opts in self.dict()['options']:
            if opts['type'] == "SBC":
                opts.setdefault('sub_params', {"sub_args": opts['args']})
                for sub_opts in opts['Options']:
                    opts['sub_params'][sub_opts['name']] = sub_opts
            self._params[opts['name']] = opts

        self._command_headers: List[str] = []  # 依据headers与command生成一个列表，其中含有所有的命令头
        if self.headers != [""]:
            for i in self.headers:
                self._command_headers.append(i + self.command)
        elif self.command:
            self._command_headers.append(self.command)

    def _analyse_args(self, key_name, opt_args, may_args, sep, rest_text, option_dict):
        for k, v in opt_args.items():
            if isinstance(v, str):
                if sep != self.separator:
                    may_arg, may_args = split_once(may_args, sep)
                else:
                    may_arg, rest_text = self.result.split_by(sep)
                if not re.match('^' + v + '$', may_arg):
                    raise ParamsUnmatched
                if key_name not in option_dict:
                    option_dict[key_name] = {k: may_arg}
                else:
                    option_dict[key_name][k] = may_arg
                if sep == self.separator:
                    self.result.raw_texts[self.result.current_index][0] = rest_text
            else:
                may_element_index = self.result.raw_texts[self.result.current_index][1] + 1
                if type(self.result.elements[may_element_index]) is not v:
                    raise ParamsUnmatched
                if key_name not in option_dict:
                    option_dict[key_name] = {k: self.result.elements.pop(may_element_index)}
                else:
                    option_dict[key_name][k] = self.result.elements.pop(may_element_index)
        return True

    def _analyse_option(self, param, text, rest_text, option_dict) -> bool:
        opt = param['name']
        arg = param['args']
        sep = param['separator']
        name, may_args = split_once(text, sep)
        if sep == self.separator:  # 在sep等于separator的情况下name是被提前切出来的
            name = text
        if not re.match('^' + opt + '$', name):  # 先匹配选项名称
            raise ParamsUnmatched
        self.result.raw_texts[self.result.current_index][0] = rest_text
        if not arg:
            option_dict[text] = ...
            return True
        return self._analyse_args(name, arg, may_args, sep, rest_text, option_dict)

    def _analyse_subcommand(self, param, text, rest_text) -> bool:
        command = param['name']
        sep = param['separator']
        name, may_text = split_once(text, sep)
        if sep == self.separator:
            name = text
        if not re.match('^' + command + '$', name):
            raise ParamsUnmatched
        self.result.raw_texts[self.result.current_index][0] = may_text
        if sep == self.separator:
            self.result.raw_texts[self.result.current_index][0] = rest_text

        if name not in self.result.results['options']:
            self.result.results['options'][name] = {}

        subcommand = {}
        sub_params = param['sub_params']
        get_args = False
        for i in range(len(sub_params)):
            try:
                _text, _rest_text = self.result.split_by(sep)
                sub_param = sub_params.get(_text)
                if not sub_param:
                    sub_param = sub_params['sub_args']
                    for sp in sub_params:
                        if _text.startswith(sp):
                            sub_param = sub_params.get(sp)
                            break
                if sub_param.get('type'):
                    self._analyse_option(sub_param, _text, _rest_text, subcommand)
                elif not get_args:
                    get_args = self._analyse_args(name, sub_param, _text, sep, _rest_text, subcommand)
            except (IndexError, KeyError):
                continue
            except ParamsUnmatched:
                break

        if sep != self.separator:
            self.result.raw_texts[self.result.current_index][0] = rest_text
        self.result.results['options'][name].update(subcommand)

        return True

    def _analyse_header(self) -> bool:
        head_text, self.result.raw_texts[0][0] = self.result.split_by(self.separator)
        for ch in self._command_headers:
            _head_find = re.findall('^' + ch + '$', head_text)
            if not _head_find:
                continue
            self.result.results['header'] = _head_find[0]
            if self.result.results['header'] == head_text:  # 如果命令头内没有正则表达式的话findall此时相当于fullmatch
                del self.result.results['header']
            self.result.head_matched = True
            return True
        raise ParamsUnmatched

    def _analyse_main_argument(self, param, text, rest_text) -> bool:
        if isinstance(param, str):
            _param_find = re.findall('^' + param + '$', text)
            if not _param_find:
                return False
            if self.result.results.get('main_argument'):
                return True
            self.result.results['main_argument'] = _param_find[0]
            self.result.raw_texts[self.result.current_index][0] = rest_text
            return True
        else:
            try:
                # 既不是str也不是dict的情况下，认为param传入了一个类的Type
                may_element_index = self.result.raw_texts[self.result.current_index][1] + 1
                if type(self.result.elements[may_element_index]) is param:
                    self.result.results['main_argument'] = self.result.elements.pop(may_element_index)
                    return True
            except KeyError:
                pass
        return False

    def analyse_message(self, message: Union[str, MessageChain]) -> Arpamar:
        self.result: Arpamar = Arpamar()

        if isinstance(message, str):
            self.result.raw_texts.append([message, 0])
        else:
            for i, ele in enumerate(message):
                if ele.__class__.__name__ not in ("Plain", "Source", "Quote", "File"):
                    self.result.elements[i] = ele
                elif ele.__class__.__name__ == "Plain":
                    self.result.raw_texts.append([ele.text.lstrip(' '), i])

        if self.main_argument != "":
            self.result.need_marg = True  # 如果need_marg那么match的元素里一定得有main_argument

        if not self.result.raw_texts:
            self.result.results.clear()
            return self.result

        self._analyse_header()

        if self.result.head_matched:
            for i in range(len(self._params)):
                if all([t[0] == "" for t in self.result.raw_texts]):
                    break
                try:
                    _text, _rest_text = self.result.split_by(self.separator)
                    _param = self._params.get(_text)
                    if not _param:
                        _param = self._params['main_argument']
                        for p in self._params:
                            if _text.startswith(p):
                                _param = self._params.get(p)
                                break
                    if isinstance(_param, dict):
                        if _param['type'] == 'OPT':
                            self._analyse_option(_param, _text, _rest_text, self.result.results['options'])
                        elif _param['type'] == 'SBC':
                            self._analyse_subcommand(_param, _text, _rest_text)
                    else:
                        self._analyse_main_argument(_param, _text, _rest_text)
                except (IndexError, KeyError):
                    pass
                except ParamsUnmatched:
                    break

        try:
            # 如果没写options并且marg不是str的话，匹配完命令头后是进不去上面的代码的，这里单独拿一段出来
            may_element_index = self.result.raw_texts[self.result.current_index][1] + 1
            if self.result.elements and type(self.result.elements[may_element_index]) is self._params['main_argument']:
                self.result.results['main_argument'] = self.result.elements.pop(may_element_index)
        except (IndexError, KeyError):
            pass

        if self.result.head_matched and len(self.result.elements) == 0 and all(
                [t[0] == "" for t in self.result.raw_texts]) \
                and (not self.result.need_marg or
                     (self.result.need_marg and not self.result.has(
                         'help') and 'main_argument' in self.result.results)):
            self.result.matched = True
            self.result.encapsulate_result()
        else:
            self.result.results.clear()
        return self.result


class AlconnaParser(EventDecorator):
    """
    Alconna的装饰器形式
    """

    def __init__(self, *, alconna: Alconna):
        super().__init__(target_type=MessageChain)
        self.alconna = alconna

    def supply(self, target_argument: ArgumentPackage) -> Arpamar:
        if target_argument.annotation == MessageChain:
            return self.alconna.analyse_message(target_argument.value)
