# This module is in charge of generating the source code for the clesperanto Python bindings.

import json
import re
import textwrap
import warnings

# C++ types that may hold Python objects, making it unsafe to release the GIL during the call
_GIL_UNSAFE_PATTERNS = ("py::", "pybind11::", "std::function")


def _is_gil_release_safe(function_dict: dict) -> bool:
    """Check that a function never touches Python objects, so the GIL can be released.

    Both the C++ declaration and the doxygen types are checked.

    Parameters
    ----------
    function_dict : dict
        Function dictionary (json-style).

    Returns
    -------
    bool
        True if no type in the function signature can hold a Python object.
    """
    types = [function_dict.get("signature", ""), function_dict.get("return", "")]
    types += [p["type"] for p in function_dict["parameters"]]
    return not any(pattern in t for t in types for pattern in _GIL_UNSAFE_PATTERNS)


def _generate_function_wrapper(function_dict: dict, tier: int) -> str:
    """Generate pybind11 wrapper code for a single function and return it as a string.

    Parameters
    ----------
    function_dict : dict
        Function dictionary (json-style).
    tier : int
        Tier number.

    Returns
    -------
    str
        Pybind11 wrapper code for a single function.
    """
    _wrapper_func_code = """m.def(\"_{name}\", &cle::tier{tier}::{name}_func, "Call cle::tier{tier}::{name}_func from C++ CLIc.",
    py::return_value_policy::automatic_reference,{gil_release}
    {parameters_bindings});"""

    name = function_dict["name"].replace("_func", "").strip()

    # release the GIL during the CLIc call, unless the signature could hold a Python object
    gil_release = "\n    PYCLE_RELEASE_GIL,"
    if not _is_gil_release_safe(function_dict):
        warnings.warn(
            f"gencle: cle::tier{tier}::{name}_func signature contains a Python-related type "
            f"({', '.join(_GIL_UNSAFE_PATTERNS)}), binding generated without GIL release."
        )
        gil_release = ""

    # for each parameter inf function_dict["parameters"], generate a string like 'py::arg("{parameter_name}")'
    parameters_name = [p["name"] for p in function_dict["parameters"]]
    parameters_bindings = ", ".join([f'py::arg("{p}")' for p in parameters_name])
    return _wrapper_func_code.format(
        name=name,
        tier=tier,
        gil_release=gil_release,
        parameters_bindings=parameters_bindings,
    ).strip()


def generate_wrapper_file(function_list: list, tier: int) -> str:
    """Generate pybind11 wrapper code for a single tier and return it as a string.

    Parameters
    ----------
    function_list : list
        list of function diction (json-style) contained in tier.
    tier : int
        Tier number.

    Returns
    -------
    str
        Pybind11 wrapper code for a single tier.
    """
    _wrapper_file_code = """// this code is auto-generated, do not edit manually

#include "pycle_wrapper.hpp"
#include "tier{tier}.hpp"

namespace py = pybind11;

// release the GIL during CLIc calls, build with -DPYCLE_NO_GIL_RELEASE to keep it held
#ifndef PYCLE_RELEASE_GIL
#  ifndef PYCLE_NO_GIL_RELEASE
#    define PYCLE_RELEASE_GIL py::call_guard<py::gil_scoped_release>()
#  else
#    define PYCLE_RELEASE_GIL py::call_guard<>()
#  endif
#endif

auto tier{tier}_(py::module &m) -> void {{
{list_function_code}
}}
"""
    list_function_code = [_generate_function_wrapper(f, tier) for f in function_list]
    str_function_code = "\n\n\t".join(list_function_code).strip()
    _wrapper_file_code = _wrapper_file_code.format(
        tier=tier, list_function_code=str_function_code
    )
    _wrapper_file_code = re.sub(r"\t", "    ", _wrapper_file_code)
    return _wrapper_file_code.strip()


def _convert_cpp_name_to_python(name: str) -> str:
    """Convert C++ function name to Python function name.

    Parameters
    ----------
    name : str
        C++ function name.

    Returns
    -------
    str
        Python function name.
    """
    name_mapping = {
        "src": "input_image",
        "dst": "output_image",
    }
    for old, new in name_mapping.items():
        name = name.replace(old, new)
    return name


def _convert_cpp_type_to_python(type: str) -> str:
    """Convert C++ type to Python type.

    Parameters
    ----------
    type : str
        C++ type.

    Returns
    -------
    str
        Python type.
    """
    type_mapping = {
        "Array::Pointer": "Image",
        "Device::Pointer": "Device",
        "std::vector": "list",
        "std::string": "str",
        "StatisticsMap": "dict",
    }
    return next((new for old, new in type_mapping.items() if old in type), type)


def _convert_argument_from_cpp_to_python(parameter: dict) -> dict:
    """Convert argument from C++ to Python.

    Parameters
    ----------
    parameter : dict
        Parameter dictionary.

    Returns
    -------
    str
        Python argument.
    """
    name = _convert_cpp_name_to_python(parameter["name"])
    type = _convert_cpp_type_to_python(parameter["type"])
    default_value = parameter["default_value"]
    description = parameter["description"]

    # update default value for device to None
    if name == "device":
        default_value = "None"

    # add Optional if default value is set to None
    if default_value == "None":
        type = f"Optional[{type}]"

    return {
        "name": name,
        "type": type,
        "default_value": default_value,
        "description": description,
    }


def _generate_function_docstring(function_dict: dict) -> str:
    """Generate docstring for a single function and return it as a string.

    Returns
    -------
    str
        Docstring for a single function.
    """
    _docstring_code = """\"\"\"{brief_str}

    Parameters
    ----------
    {parameters_str}

    Returns
    -------
    {return_str}{references_str}
    \"\"\""""

    function_name = function_dict["name"]
    brief = function_dict["brief"]
    parameters = function_dict["parameters"]
    links = function_dict["link"]

    # if link is not empty, add a new line and indent it with 4 spaces
    references_title = "\n\n\tReferences\n\t----------\n" if len(links) > 0 else ""
    references_list = [f"\t[{i+1}] {l}" for i, l in enumerate(links)]
    references_str = "\n".join(references_list)
    references_str = references_title + references_str

    # build parameters string
    parameters_list = []
    for p in parameters:
        p = _convert_argument_from_cpp_to_python(p)
        param_name = p["name"].strip()
        param_type = p["type"].strip()
        default_value = p["default_value"].strip()
        default_str = f"(= {default_value})" if len(default_value) > 0 else ""
        description = p["description"]
        parameters_list.append(
            f"{param_name}: {param_type} {default_str}\n\t\t{description}"
        )
    parameters_list.append(parameters_list.pop(0))
    parameters_str = "\n\t".join(parameters_list)

    # return
    return_str = _convert_cpp_type_to_python(function_dict["return"])

    brief_str = ""
    if brief:
        brief_str = "\n    ".join(
            textwrap.wrap(brief, 80, break_long_words=False, break_on_hyphens=False)
        )

    return _docstring_code.format(
        brief_str=brief_str,
        parameters_str=parameters_str,
        return_str=return_str,
        references_str=references_str,
    )


def _generate_decorator(function_dict: dict) -> str:
    """Generate decorator parameter for a function.

    Parameters
    ----------
    function_dict : dict
        Function dictionary (json-style).

    Returns
    -------
    str
        Code for a single function as pybind11 code.
    """
    priority = (
        function_dict["priority"].replace("'", '"')
        if function_dict["priority"] != ""
        else None
    )
    category = (
        function_dict["category"].replace("'", '"')
        if function_dict["category"] != ""
        else None
    )
    category_defines = f"categories=[{category}]" if category else ""
    priority_defines = f"priority={priority}" if priority else ""
    args = [a for a in (category_defines, priority_defines) if a]
    if not args:
        return ""

    single_line = f"@plugin_function({', '.join(args)})"
    if len(single_line) <= _MAX_LINE_LENGTH:
        return f"({', '.join(args)})"

    trailing_comma = "," if len(args) > 1 else ""
    lines = ["("]
    for i, arg in enumerate(args):
        is_last = i == len(args) - 1
        comma = trailing_comma if is_last else ","
        candidate = f"    {arg}"
        if len(candidate) <= _MAX_LINE_LENGTH:
            lines.append(candidate + comma)
        else:
            # only a categories=[...] argument can be too long here
            name, items_part = arg.split("[", 1)
            items = [i.strip() for i in items_part.rstrip("]").split(",") if i.strip()]
            lines.append(f"    {name}[")
            lines.extend(f"        {item}," for item in items)
            lines.append("    ]" + comma)
    lines.append(")")
    return "\n".join(lines)


def _generate_deprecated_decorator(function_dict: dict) -> str:
    """Generate the deprecation decorator line for a function, if needed."""
    deprecation = function_dict.get("deprecation", {})
    if not deprecation:
        return ""

    if isinstance(deprecation, list):
        message = " ".join(deprecation).strip()
    else:
        message = deprecation.strip()
    if not message:
        return ""

    function_name = function_dict["name"].replace("_func", "").strip()
    full_message = f"{function_name}: {message}"
    quoted_message = json.dumps(full_message)

    single_line = f"@deprecated({quoted_message})"
    if len(single_line) <= _MAX_LINE_LENGTH:
        return f"{single_line}\n"
    return f"@deprecated(\n    {quoted_message}\n)\n"


_MAX_LINE_LENGTH = 88


def _format_signature(function_name: str, parameters: list, return_type: str) -> str:
    """Format a function signature, collapsing it to one line when it fits.

    Mimics black's line-length rule: a signature that fits within
    ``_MAX_LINE_LENGTH`` is kept on a single line, otherwise it is split
    with one parameter per line and a trailing comma.

    Parameters
    ----------
    function_name : str
        Name of the function.
    parameters : list
        List of formatted "name: type = default" parameter strings.
    return_type : str
        Return type annotation.

    Returns
    -------
    str
        Formatted "def ...(...) -> ...:" signature.
    """
    single_line = f"def {function_name}({', '.join(parameters)}) -> {return_type}:"
    if len(single_line) <= _MAX_LINE_LENGTH and "\n" not in single_line:
        return single_line

    parameters_one_line = f"    {', '.join(parameters)}"
    if len(parameters_one_line) <= _MAX_LINE_LENGTH:
        return f"def {function_name}(\n{parameters_one_line}\n) -> {return_type}:"

    joined_parameters = ",\n    ".join(parameters)
    return f"def {function_name}(\n    {joined_parameters},\n) -> {return_type}:"


def _format_return_call(function_name: str, arguments: list) -> str:
    """Format the backend call in the ``return`` statement.

    Mimics black's line-length rule: the call is kept on a single line
    when it fits, otherwise its arguments are moved to an indented block,
    either on one line or one argument per line if still too long.

    Parameters
    ----------
    function_name : str
        Name of the function (without the leading underscore).
    arguments : list
        List of formatted argument strings.

    Returns
    -------
    str
        Formatted "return _get_backend()._name(...)" statement.
    """
    call_prefix = f"return _get_backend()._{function_name}("
    single_line = f"    {call_prefix}{', '.join(arguments)})"
    if len(single_line) <= _MAX_LINE_LENGTH:
        return single_line

    arguments_one_line = f"        {', '.join(arguments)}"
    if len(arguments_one_line) <= _MAX_LINE_LENGTH:
        return f"    {call_prefix}\n{arguments_one_line}\n    )"

    joined_arguments = ",\n        ".join(arguments)
    return f"    {call_prefix}\n        {joined_arguments},\n    )"


def _generate_python_function(function_dict: dict) -> str:
    """Generate Python function code for a single function and return it as a string.

    Parameters
    ----------
    function_dict : dict
        Function dictionary.

    Returns
    -------
    str
        Python function code for a single function.
    """
    _python_func_code = """{deprecation_decorator}@plugin_function{decorator}
{signature}
    {docstring_str}
{return_call}
"""

    function_name = function_dict["name"].replace("_func", "").strip()
    return_type = _convert_cpp_type_to_python(function_dict["return"])
    _docstring_str = _generate_function_docstring(function_dict)
    decorator = _generate_decorator(function_dict)
    deprecation_decorator = _generate_deprecated_decorator(function_dict)

    arguments_list = []
    python_parameters_list = []
    for p in function_dict["parameters"]:
        p = _convert_argument_from_cpp_to_python(p)
        param_name = p["name"]
        param_type = p["type"]
        default = p["default_value"].strip().replace("'", '"')
        default_value = f" = {default}" if len(default) > 0 else ""
        python_parameters_list.append(f"{param_name}: {param_type}{default_value}")
        arguments_list.append(
            param_name
            if param_type not in ["int", "float", "str"]
            else f"{param_type}({param_name})"
        )
    # put the first element of python_parameters_list at the end of the list
    python_parameters_list.append(python_parameters_list.pop(0))

    signature = _format_signature(function_name, python_parameters_list, return_type)
    return_call = _format_return_call(function_name, arguments_list)

    return _python_func_code.format(
        decorator=decorator,
        deprecation_decorator=deprecation_decorator,
        signature=signature,
        docstring_str=_docstring_str,
        return_call=return_call,
    ).strip()



def generate_api_functions_list(function_list: list) -> str:
    """Generate __all__ list for the Python module.

    Parameters
    ----------
    function_list : list
        List of function dictionaries.

    Returns
    -------
    str
        __all__ list for the Python module.
    """
    function_names = [
        f'"{f["name"].replace("_func", "").strip()}"' for f in function_list
    ]
    # generate a string __all__ = [ "func1", "func2", ... ], one item per line
    # if it does not fit on a single line (matches black's line-length rule)
    single_line = f"__all__ = [{', '.join(function_names)}]"
    if len(single_line) <= _MAX_LINE_LENGTH:
        return single_line
    joined_names = ",\n    ".join(function_names)
    return f"__all__ = [\n    {joined_names},\n]"



def generate_python_file(function_list: list, tier: int) -> str:
    """Generate Python code for a single tier and return it as a string.

    Parameters
    ----------
    function_list : list
        List of function dictionaries.
    tier : int
        Tier number.

    Returns
    -------
    str
        Python code for a single tier.
    """
    _python_code = """#
# This code is auto-generated from CLIc 'cle::tier{tier}.hpp' file, do not edit manually.
#

import warnings
from typing import Optional

import numpy as np

from ._array import Image
from ._backend import _get_backend
from ._core import Device
from ._decorators import plugin_function
from ._utils import deprecated


{python_functions_str}


{api_functions_list}
"""
    api_functions_list = generate_api_functions_list(function_list)
    python_functions_list = [_generate_python_function(f) for f in function_list]
    python_functions_str = "\n\n\n".join(python_functions_list)
    _python_code = _python_code.format(
        tier=tier, python_functions_str=python_functions_str, api_functions_list=api_functions_list
    )
    _python_code = re.sub(r"\t", "    ", _python_code)
    return _python_code.strip()
