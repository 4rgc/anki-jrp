from collections.abc import Callable, Generator
from enum import Enum, auto

import aqt.utils
from aqt.editor import Editor

from . import global_vars
from ..pylib.converter import convert
from ..pylib.html_processing import strip_html
from ..pylib.mecab import Mecab
from ..pylib.output import fmt_jrp, fmt_migaku
from ..pylib.segments import parse_jrp, parse_migaku

_js_esc = str.maketrans({
    "\r": "\\r",
    "\n": "\\n",
    "\"": "\\\"",
    "\\": "\\\\",
})


class OutputType(Enum):
    DEFAULT = auto()
    MIGAKU = auto()


class ConversionType(Enum):
    GENERATE = auto()
    READINGS = auto()  # TODO implement
    REMOVE = auto()


def _replace(edit: Editor, transform: Callable[[str], str]):
    def inject_html(new_html: str):
        edit.web.page().runJavaScript(f"""
        editable = getCurrentField().activeInput
        editable.fieldHTML = \"{transform(new_html).translate(_js_esc)}\"
        editable.caretToEnd()""")

    edit.web.page().runJavaScript("getCurrentField().activeInput.fieldHTML", lambda html: inject_html(html))


def _convert(edit: Editor, out_type: OutputType, conv_type: ConversionType):
    parser = parse_migaku if out_type == OutputType.MIGAKU else parse_jrp
    formatter = fmt_migaku if out_type == OutputType.MIGAKU else fmt_jrp

    def gen_lines(val: str) -> Generator[str]:
        lines = strip_html(val)
        yield from ("".join(u.text() for u in parser(line)) for line in lines)

    def transform(val: str) -> str:
        if conv_type == ConversionType.REMOVE:
            return "<br>".join(gen_lines(val))
        else:
            prefs = global_vars.prefs
            dic = global_vars.dictionary
            if not dic:
                aqt.utils.showWarning("Dictionary is not (yet) loaded, can't convert.")

            return "<br>".join(formatter(convert(line, prefs.convert, Mecab(), dic)) for line in gen_lines(val))

    _replace(edit, transform)


def inject_buttons(buttons: list[str], edit: Editor):
    buttons.append(edit.addButton(
        icon=None,
        cmd="jrp_generate_default",
        func=lambda e: _convert(e, OutputType.DEFAULT, ConversionType.GENERATE),
        tip="[F2] (Re)generate readings and accents with default syntax.",
        keys="F2")
    )
    buttons.append(edit.addButton(
        icon=None,
        cmd="jrp_remove_default",
        func=lambda e: _convert(e, OutputType.DEFAULT, ConversionType.REMOVE),
        tip="[Ctrl+F2] Restore original text from default syntax.",
        keys="Ctrl+F2")
    )
    buttons.append(edit.addButton(
        icon=None,
        cmd="jrp_generate_migaku",
        func=lambda e: _convert(e, OutputType.MIGAKU, ConversionType.GENERATE),
        tip="[F3] (re)generate readings and accents with Migaku syntax.",
        keys="F3")
    )
    buttons.append(edit.addButton(
        icon=None,
        cmd="jrp_remove_migaku",
        func=lambda e: _convert(e, OutputType.MIGAKU, ConversionType.REMOVE),
        tip="[Ctrl+F3] Restore original text from Migaku syntax.",
        keys="Ctrl+F3")
    )
