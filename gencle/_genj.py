# This module is in charge of generating the source code for the clesperanto Java bindings. 


native_func_code_template = """
{return_type} Tier{tier}::{func_name}({argument_list})
{{
    return {return_type}{{ cle::tier{tier}::{func_name}_func({argument_call}) }};
}}
"""

native_func_header_template = """static {return_type} {func_name}({argument_list});"""

def _generate_arguments( args ):
    """ args is a list of dictionaries, each dict has the field `name`, `type`, `default_value`, `description` and 'default' """

    argument_list = []
    for arg in args:
        
        arg_name = arg["name"]
        arg_type = arg["type"]
        arg_call = arg["name"]
        arg_default = arg["default_value"]

        if "Device::Pointer" in arg_type:
            arg_type = arg_type.replace("Device::Pointer", "DeviceJ"   )
            arg_call = f"{arg_call}.get()"
        if "Array::Pointer" in arg_type:
            arg_type = arg_type.replace("Array::Pointer", "ArrayJ"   )
            arg_call = f"{arg_call}.get()"

        argument_list.append({"name": arg_name, "type": arg_type, "call": arg_call, "default": arg_default})
    return argument_list


def _generate_native_full( tier, function_dict ):
    """ Generates the code for the full version of the native function. This version has all the arguments and the return type.
        It returns the header and the source code of the function.
    """
    argument_dict = _generate_arguments( function_dict["parameters"] )
    return_type = function_dict["return"].replace("Device::Pointer", "DeviceJ").replace("Array::Pointer", "ArrayJ")

    argument_list = []
    argument_call = []
    for arg in argument_dict:
        arg_string = arg["type"] + " " + arg["name"]
        argument_list.append(arg_string)
        argument_call.append(arg["call"])
    argument_list = ", ".join(argument_list)
    argument_call = ", ".join(argument_call)
    
    code = native_func_code_template.format(return_type=return_type, tier=tier, func_name=function_dict["name"],
                                                argument_list=argument_list, argument_call=argument_call)
    header = native_func_header_template.format(return_type=return_type, func_name=function_dict["name"],
                                                argument_list=argument_list)
    
    return code, header


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
        code_full, header_full = _generate_native_full( tier, func )

        func_header_str = "".join(header_full)
        functions_headers.append(func_header_str)

        func_code_str = "".join(code_full)
        functions_code.append(func_code_str)

    functions_headers = "\n\t".join(functions_headers)
    header = class_header_template.format(tier=tier, functions_headers=functions_headers)

    functions_code = "".join(functions_code)
    code = class_code_template.format(tier=tier, functions_code=functions_code)

    return header, code


def merger_header( header_list ):
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


def _snake_to_camel(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

# def _generate_java_function(function_dict):
#     function_template = """
# 	public static {return_type_1} {java_function_name}({java_function_parameters}) {{
# 		{parameter_null_checks} 
#             {dst_null_checks}
# 		return {return_type_2}(net.clesperanto._internals.kernelj.Tier{tier_idx}.{native_function_name}({native_function_parameters});
# 	}}
#     """

#     tier_idx = str(0)

#     native_function_name = function_dict[0]["name"]
#     java_function_name = _snake_to_camel(native_function_name)

#     return_type_1 = function_dict[0]["return"]
#     return_type_2 = return_type_1
#     if return_type_1 == "Array::Pointer" :
#         return_type_1 = "ArrayJ"
#         return_type_2 = "new ArrayJ"

#     null_check = []
#     dst_null_check = []
#     java_function_parameters = []
#     native_function_parameters = []
#     for param in function_dict[0]["parameters"]:

        
#         param_call = ""
#         param_type = param["type"]
#         if param_type.find("Device::Pointer") != -1:
#             param_type = "DeviceJ"
#             param_call = f".getRaw()"
#         elif param_type.find("Array::Pointer") != -1:
#             param_type = "ArrayJ"
#             param_call = f".getRaw()"
#         elif param_type.find("std::vector") != -1:
#             param_type = "ArrayList<Float>"



#         param_name = param["name"]
#         if param_name.find("src") != -1:
#             param_name = param_name.replace("src", "input")
#         elif param_name.find("dst") != -1:
#             param_name = param_name.replace("dst", "output")

#         if param["type"].find("const") != -1 and param["type"].find("::Pointer") != -1:
#             null_check.append(f'Objects.requireNonNull({param_name}, "{param_name} cannot be null");')
#         if param["default_value"] == "None" and param["type"].find("::Pointer") != -1:
#             dst_null_check.append(f'{param_type} {param_name} = {param_name} == null ? null : {param_name}{param_call};')

        
#         java_function_parameters += [f"{param_type} {param_name}"] 
#         native_function_parameters += [f"{param_name}{param_call}"]

#     parameter_null_checks = "\n\t\t".join(null_check)
#     dst_null_checks = "\n\t\t".join(dst_null_check)
#     java_function_parameters = ", ".join(java_function_parameters)
#     native_function_parameters = ", ".join(native_function_parameters)


#     return function_template.format(java_function_name=java_function_name, return_type_1=return_type_1, return_type_2=return_type_2, tier_idx=tier_idx, native_function_name=native_function_name, java_function_parameters=java_function_parameters, native_function_parameters=native_function_parameters,dst_null_checks=dst_null_checks, parameter_null_checks=parameter_null_checks)


def _generate_java_function(tier_idx, function_dict):
    function_template = """
    public static {return_type_1} {java_function_name}({java_function_parameters}) {{
        {parameter_null_checks}
        {dst_null_checks}
        return {return_type_2}(net.clesperanto._internals.kernelj.Tier{tier_idx}.{native_function_name}({native_function_parameters}));
    }}
    """
    native_function_name = function_dict["name"]
    java_function_name = _snake_to_camel(native_function_name)

    return_type = function_dict["return"]
    return_type_1, return_type_2 = ("ArrayJ", "new ArrayJ") if return_type == "Array::Pointer" else (return_type, "")

    null_checks, dst_null_checks, java_params, native_params = [], [], [], []

    for param in function_dict["parameters"]:
        param_type = param["type"].replace("Device::Pointer", "DeviceJ").replace("Array::Pointer", "ArrayJ").replace("const ", "").replace("&", "")
        param_call = ".getRaw()" if "Pointer" in param["type"] else ""
        param_type = "ArrayList<Float>" if "std::vector" in param_type else param_type

        param_name = param["name"].replace("src", "input").replace("dst", "output")
        if "const" in param["type"] and "::Pointer" in param["type"]:
            null_checks.append(f'Objects.requireNonNull({param_name}, "{param_name} cannot be null");')
        if param["default_value"] == "None" and "::Pointer" in param["type"]:
            dst_null_checks.append(f'{param_name} = {param_name} == null ? null : {param_name}{param_call};')
            param_call = ""

        java_params.append(f"{param_type} {param_name}")
        native_params.append(f"{param_name}{param_call}")

    parameter_null_checks = "\n\t\t".join(null_checks)
    dst_null_checks_str = "\n\t\t".join(dst_null_checks)
    java_function_parameters = ", ".join(java_params)
    native_function_parameters = ", ".join(native_params)

    return function_template.format(
        java_function_name=java_function_name,
        return_type_1=return_type_1,
        return_type_2=return_type_2,
        tier_idx=tier_idx,
        native_function_name=native_function_name,
        java_function_parameters=java_function_parameters,
        native_function_parameters=native_function_parameters,
        dst_null_checks=dst_null_checks_str,
        parameter_null_checks=parameter_null_checks
    )


def _generate_java_class(tier_idx, functions):
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