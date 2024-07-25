# This module is in charge of generating the source code for the clesperanto Java bindings. 

#
# The following functions are used to generate the native code for the Java bindings.
#

def __cpp_return_guard(parameter: str):
    mapping = {
        "Array::Pointer": ("ArrayJ", "ArrayJ{", "}")
    }
    return mapping.get(parameter, (parameter, "", ""))



def _cpp_function_parameters(parameters):
    def _replace_type(param_type):
        replacements = {
            "const ": "",
            "&": "",
            "Device::Pointer": "DeviceJ *",
            "Array::Pointer": "ArrayJ *",
            "std::string": "String"
        }
        for old, new in replacements.items():
            param_type = param_type.replace(old, new)
        return param_type
    
    function_parameters = []
    for p in parameters:
        param_name = p["name"]
        param_type = _replace_type(p["type"])
        function_parameters.append(f"{param_type} {param_name}")
    return ", ".join(function_parameters)


def _cpp_call_parameters(parameters):
    def _is_pointer_type(param_type):
        return "::Pointer" in param_type

    def _generate_param_call(param_name, param_type, default_value):
        param_call = "->get()" if _is_pointer_type(param_type) else ""
        if default_value == "None" and _is_pointer_type(param_type):
            return f'{param_name} == nullptr ? nullptr : {param_name}{param_call}'
        return f"{param_name}{param_call}"
    
    native_call = []
    for p in parameters:
        cpp_parameter_call = _generate_param_call(p["name"], p["type"], p["default_value"])
        native_call.append(cpp_parameter_call)
    return ", ".join(native_call)


def _generate_native_functions( tier, function_dict ):
    native_func_code_template = """
{return_type} Tier{tier}::{func_name}({argument_list})
{{
    return {return_prefix}cle::tier{tier}::{func_name}_func({argument_call}){return_suffix};
}}
"""
    native_func_header_template = """static {return_type} {func_name}({argument_list});"""

    func_name = function_dict["name"]
    return_type, return_prefix, return_suffix = __cpp_return_guard(function_dict["return"])
    argument_list = _cpp_function_parameters(function_dict["parameters"])
    argument_call = _cpp_call_parameters(function_dict["parameters"])
    cpp_native = native_func_code_template.format(return_type=return_type, tier=tier, func_name=func_name,
                                                argument_list=argument_list, argument_call=argument_call,
                                                return_prefix=return_prefix, return_suffix=return_suffix)
    cpp_header = native_func_header_template.format(return_type=return_type, func_name=func_name,
                                                argument_list=argument_list)
    return cpp_native, cpp_header


def generate_native_tier_code( tier, functions ):
    """ For a given tier and list of dictionary describing the functions, it generates the header and source code for the tier."""
    class_header_template = """
class Tier{tier}
{{
public:
    {functions_headers}
}};
"""

    class_code_template = """
#include "kernelj.hpp"
#include "tier{tier}.hpp"
{functions_code}
"""

    functions_headers = []
    functions_code = []
    for func in functions:
        code_full, header_full = _generate_native_functions( tier, func )

        func_header_str = "".join(header_full)
        functions_headers.append(func_header_str)

        func_code_str = "".join(code_full)
        functions_code.append(func_code_str)

    functions_headers = "\n\t".join(functions_headers)
    header = class_header_template.format(tier=tier, functions_headers=functions_headers)

    functions_code = "".join(functions_code)
    code = class_code_template.format(tier=tier, functions_code=functions_code)

    return header, code


def merger_classes_in_header( header_list ):
    """ Merges the header code into one header."""
    header_file = """
#ifndef __INCLUDE_KERNEL_HPP
#define __INCLUDE_KERNEL_HPP

#include "clesperantoj.hpp"

{header_str}

#endif // __INCLUDE_KERNEL_HPP
"""    
    
    header_str = "\n".join(header_list)
    return header_file.format(header_str=header_str)

#
# The following functions are used to generate the java code for the Java bindings.
#

def _java_snake_to_camel(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def _java_null_check(parameters):
    null_checks = [
        f'Objects.requireNonNull({p["name"]}, "{p["name"]} cannot be null");'
        for p in parameters
        if "const" in p["type"] and "::Pointer" in p["type"]
    ]
    return "\n\t\t".join(null_checks)


def _java_function_parameters(parameters):
    def _replace_java_type(param_type):
        replacements = {
            "const ": "",
            "&": "",
            "Device::Pointer": "DeviceJ",
            "Array::Pointer": "ArrayJ",
            "std::string": "String"
        }
        for old, new in replacements.items():
            param_type = param_type.replace(old, new)
        return param_type
    
    function_parameters = []
    for p in parameters:
        param_name = p["name"]
        param_type = _replace_java_type(p["type"])
        function_parameters.append(f"{param_type} {param_name}")
    return ", ".join(function_parameters)



def _java_call_parameters(parameters):
    def _is_pointer_type(param_type):
        return "::Pointer" in param_type

    def _generate_java_param_call(param_name, param_type, default_value):
        param_call = ".getRaw()" if _is_pointer_type(param_type) else ""
        if default_value == "None" and _is_pointer_type(param_type):
            return f'{param_name} == null ? null : {param_name}{param_call}'
        return f"{param_name}{param_call}"
    
    native_call = []
    for p in parameters:
        cpp_parameter_call = _generate_java_param_call(p["name"], p["type"], p["default_value"])
        native_call.append(cpp_parameter_call)
    return ", ".join(native_call)


def _java_return_guard(parameter):
    mapping = {
        "Array::Pointer": ("ArrayJ", "new ArrayJ(", ", device)")
    }
    return mapping.get(parameter, (parameter, "", ""))


def _generate_java_function(tier_idx, function_dict):
    function_template = """
    public static {return_type} {java_function_name}({function_parameters}) {{
        {parameter_null_checks}
        return {return_prefix}net.clesperanto._internals.kernelj.Tier{tier_idx}.{native_function_name}({call_parameters}){return_suffix};
    }}
    """
    native_function_name = function_dict["name"]
    java_function_name = _java_snake_to_camel(function_dict["name"])
    return_type, return_prefix, return_suffix = _java_return_guard(function_dict["return"])
    parameter_null_checks = _java_null_check(function_dict["parameters"])
    function_parameters = _java_function_parameters(function_dict["parameters"])
    call_parameters = _java_call_parameters(function_dict["parameters"])
    function = function_template.format( 
        return_type=return_type,
        java_function_name=java_function_name,
        tier_idx=tier_idx,
        native_function_name=native_function_name,
        function_parameters=function_parameters,
        parameter_null_checks=parameter_null_checks,
        call_parameters=call_parameters,
        return_prefix=return_prefix,
        return_suffix=return_suffix
    )
    return function.replace("src", "input").replace("dst", "output")


def generate_java_class(tier_idx, functions):
    class_template = """
package net.clesperanto.kernels;

import java.util.Objects;

import net.clesperanto.core.ArrayJ;
import net.clesperanto.core.DeviceJ;

/**
 * Class containing all functions of tier {tier_idx} category
 */
public class Tier{tier_idx} {{
{functions}
}}
"""
    functions_str = "".join([_generate_java_function(tier_idx, function) for function in functions])
    return class_template.format(tier_idx=tier_idx, functions=functions_str)