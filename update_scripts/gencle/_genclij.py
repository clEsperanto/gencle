# This module is in charge of generating the source code for the clesperanto CLIJ3 code.

#
# The following functions are used to generate the native code for the Java FIJI pluging CLIJ.
#

import os


def get_function_name(line):
    """extract and return the function name from a Java method signature line."""
    return line.split("(")[0].split(" ")[-1]


def get_return_type(line):
    return " ".join(line.split("(")[0].split(" ")[:-1])


def get_parameters(line):
    return [f.strip() for f in line.split("(")[1].split(")")[0].split(",")]


import re


def camel_to_snake(name):
    # Replace all uppercase letters with _ followed by the lowercase letter
    s1 = re.sub("([A-Z])", r"_\1", name)
    # Convert the entire string to lowercase
    return s1.lower()


def make_java_types(list_of_parameters):
    definitions = []
    calls = []
    for p in list_of_parameters:
        definition_type = p.split(" ")[0]
        parameter_name = p.split(" ")[1]
        if definition_type == "ArrayJ":
            definitions.append("Object " + parameter_name)
            calls.append("push(" + parameter_name + ")")
        else:
            definitions.append(definition_type + " " + parameter_name)
            calls.append(parameter_name)

    return definitions, calls


def function_wrapper(line, tier):
    camel_function_name = get_function_name(line)
    snake_function_name = camel_to_snake(camel_function_name)
    return_type = get_return_type(line).replace("static ", "")
    parameters = get_parameters(line)

    all_but_first_parameters = parameters[1:]

    param_definitions, param_values = make_java_types(all_but_first_parameters)

    param_definitions = ", ".join(param_definitions)
    param_values = ", ".join(param_values)

    return f"""
    {return_type} {snake_function_name}({param_definitions}) {{
        return Tier{tier}.{camel_function_name}(device, {param_values});
    }}
"""


def list_tier_files(folder: str) -> list:
    # list all the files in the folder that start with Tier and end with .java
    tier_list = [
        f for f in os.listdir(folder) if f.startswith("Tier") and f.endswith(".java")
    ]
    return tier_list


def get_tier_number(file_name):
    return int(file_name.split("Tier")[1].split(".java")[0])


def generate_clij_code_per_tier(files, tiers):
    output = ""
    for tier, content in zip(tiers, files):
        # List to store lines starting with "public static "
        matching_lines = []

        # Process each line
        for line in content.splitlines():
            stripped_line = line.lstrip()  # Remove leading spaces
            if stripped_line.startswith("public static "):
                matching_lines.append(stripped_line)

        for line in matching_lines:
            output = output + function_wrapper(line, tier)
    return output


def update_clij3_code(content, code):
    # Find the start and end indices of the block
    start_index = None
    end_index = None
    start_marker = "/* BEGIN AUTO-GENERATED FUNCTIONS */"
    end_marker = "/* END AUTO-GENERATED FUNCTIONS */"

    # Find the index positions
    start_index = content.find(start_marker)
    end_index = content.find(end_marker)

    # add line return to the code before and after
    code = "\n" + code + "\n"

    # Replace the block
    updated_content = content
    if start_index == -1 or end_index == -1:
        print("Markers not found in the file.")
    else:
        # Calculate the positions to replace the content between the markers
        start_index += len(start_marker)

        # Replace the content between the markers
        updated_content = content[: start_index + 1] + code + content[end_index - 1 :]

    return updated_content
