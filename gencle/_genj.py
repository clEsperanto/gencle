import textwrap

# This is a Python module in charge of generating the Java source code for the 
# clesperanto Java bindings. It is called by the gencle.py script.

native_func_code_template = """
{return_type} Tier{tier}::{func_name}({argument_list})
{{
    return {return_type}{{ cle::tier{tier}::{func_name}_func({argument_call}) }};
}}
"""

native_func_header_template = """static {return_type} {func_name}({argument_list});"""

def generate_arguments( args ):
    """ args is a list of dictionaries, each dict has the field `name`, `type`, `default_value`, and `description` """

    argument_list = []
    for arg in args:
        
        arg_name = arg["name"]
        arg_type = arg["type"]
        arg_call = arg["name"]

        if "Device::Pointer" in arg_type:
            arg_type = arg_type.replace("Device::Pointer", "DeviceJ"   )
            arg_call = f"{arg_call}.get()"
        if "Array::Pointer" in arg_type:
            arg_type = arg_type.replace("Array::Pointer", "ArrayJ"   )
            arg_call = f"{arg_call}.get()"

        argument_list.append({"name": arg_name, "type": arg_type, "call": arg_call})
    return argument_list


def generate_native_full( tier, function_dict ):

    argument_dict = generate_arguments( function_dict["parameters"] )
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
    

def generate_native_short( tier, function_dict ):

    argument_dict = generate_arguments( function_dict["parameters"] )
    return_type = function_dict["return"].replace("Device::Pointer", "DeviceJ").replace("Array::Pointer", "ArrayJ")

    argument_list = []
    argument_call = []
    for arg in argument_dict:
        arg_string = arg["type"] + " " + arg["name"]
        if arg["name"] != "dst" and arg["name"] != "dst1":
            argument_list.append(arg_string)
            argument_call.append(arg["call"])
        else:
            argument_call.append("nullptr")
    argument_list = ", ".join(argument_list)
    argument_call = ", ".join(argument_call)
    
    code = native_func_code_template.format(return_type=return_type, tier=tier, func_name=function_dict["name"],
                                                argument_list=argument_list, argument_call=argument_call)
    header = native_func_header_template.format(return_type=return_type, func_name=function_dict["name"],
                                                argument_list=argument_list)
    
    return code, header


def generate_tier_code( tier, functions ):
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
        code_full, header_full = generate_native_full( tier, func )
        code_short, header_short = generate_native_short( tier, func )

        if header_full == header_short:
            header_short = ""
            code_short = ""

        func_header_str = "\n\t".join([header_short, header_full])
        functions_headers.append(func_header_str)

        func_code_str = "".join([code_short, code_full])
        functions_code.append(func_code_str)

    functions_headers = "\n\t".join(functions_headers)
    header = class_header_template.format(tier=tier, functions_headers=functions_headers)

    functions_code = "".join(functions_code)
    code = class_code_template.format(tier=tier, functions_code=functions_code)

    return header, code


def merger_header( header_list ):

    header_file = """
#ifndef __INCLUDE_KERNELJ_HPP
#define __INCLUDE_KERNELJ_HPP

#include "clesperantoj.hpp"

{header_str}

#endif // __INCLUDE_KERNELJ_HPP
"""    
    
    header_str = "\n".join(header_list)
    return header_file.format(header_str=header_str)