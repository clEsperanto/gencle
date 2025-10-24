# This module is in charge of generating the source code for the clesperanto Python bindings.

import textwrap, re


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
    py::return_value_policy::automatic_reference,
    {parameters_bindings});"""

    name = function_dict["name"].replace("_func", "").strip()

    # for each parameter inf function_dict["parameters"], generate a string like 'py::arg("{parameter_name}")'
    parameters_name = [p["name"] for p in function_dict["parameters"]]
    parameters_bindings = ", ".join([f'py::arg("{p}")' for p in parameters_name])
    return _wrapper_func_code.format(
        name=name, tier=tier, parameters_bindings=parameters_bindings
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


# def _convert_cpp_type_to_python(type: str) -> str:
#     """Convert C++ type to Python type.

#     Parameters
#     ----------
#     type : str
#         C++ type.

#     Returns
#     -------
#     str
#         Python type.
#     """
#     type_mapping = {
#         "Array::Pointer": "Image",
#         "Device::Pointer": "Device",
#         "std::vector": "list",
#         "std::vector<Array::Pointer>": "list[Image]",
#         "std::string": "str",
#         "StatisticsMap": "dict",
#     }
#     return next((new for old, new in type_mapping.items() if old in type), type)

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
    # Strip whitespace
    type = type.strip()
    
    # Exact matches first (order matters for specificity)
    type_mapping = {
        "Array::Pointer": "Image",
        "Device::Pointer": "Device",
        "std::vector<Array::Pointer>": "List[Image]",
        "std::vector": "List",
        "std::string": "str",
        "StatisticsMap": "dict",
    }
    
    # Check for exact match first
    if type in type_mapping:
        return type_mapping[type]
    
    # Check for partial matches (for complex types)
    for cpp_type, python_type in type_mapping.items():
        if cpp_type in type:
            return python_type
    
    # Return original type if no mapping found
    return type

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

    decorator_defines = ""
    if len(category_defines) > 0 and len(priority_defines) > 0:
        decorator_defines = f"({category_defines}, {priority_defines})"
    elif len(category_defines) > 0:
        decorator_defines = f"({category_defines})"
    elif len(priority_defines) > 0:
        decorator_defines = f"({priority_defines})"
    return decorator_defines


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
    _python_func_code = """@plugin_function{decorator}
def {function_name}(
    {python_parameters_str}
) -> {return_type}:
    {docstring_str}
    return clic._{function_name}({arguments_str})
"""

    function_name = function_dict["name"].replace("_func", "").strip()
    return_type = _convert_cpp_type_to_python(function_dict["return"])
    _docstring_str = _generate_function_docstring(function_dict)
    decorator = _generate_decorator(function_dict)

    arguments_list = []
    python_parameters_list = []
    for p in function_dict["parameters"]:
        p = _convert_argument_from_cpp_to_python(p)
        param_name = p["name"]
        param_type = p["type"]
        default = p["default_value"].strip()
        default_value = f" ={default}" if len(default) > 0 else ""
        python_parameters_list.append(f"{param_name}: {param_type}{default_value}")
        arguments_list.append(
            param_name
            if param_type not in ["int", "float", "str"]
            else f"{param_type}({param_name})"
        )
    # put the first element of python_parameters_list at the end of the list
    python_parameters_list.append(python_parameters_list.pop(0))
    python_parameters_str = ",\n\t".join(python_parameters_list)
    arguments_str = ", ".join(arguments_list)

    # deprecation_warning = ''
    # if len(function_dict['deprecation']) > 0:
    #     deprecation_warning = f"\n\twarnings.warn(\"pyclesperanto.{function_name}: {function_dict['deprecation'][0]}\", DeprecationWarning,)"

    return _python_func_code.format(
        decorator=decorator,
        function_name=function_name,
        python_parameters_str=python_parameters_str,
        return_type=return_type,
        docstring_str=_docstring_str,
        arguments_str=arguments_str,
    ).strip()


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

import importlib
import warnings
from typing import Optional, List

import numpy as np

from ._array import Image
from ._core import Device
from ._decorators import plugin_function

clic = importlib.import_module('._pyclesperanto', package='pyclesperanto')

{python_functions_str}
"""

    python_functions_list = [_generate_python_function(f) for f in function_list]
    python_functions_str = "\n\n".join(python_functions_list)
    _python_code = _python_code.format(
        tier=tier, python_functions_str=python_functions_str
    )
    _python_code = re.sub(r"\t", "    ", _python_code)
    return _python_code.strip()
