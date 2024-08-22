import gencle
import glob, os, re

# manage folder paths
PYCLE_FOLDER = '/data/clesperanto/pyclesperanto'
WRAPPER_FOLDER = os.path.join(PYCLE_FOLDER, 'src/wrapper')
PYTHON_FOLDER = os.path.join(PYCLE_FOLDER, 'pyclesperanto')

code_list, tier_list = gencle.read_tier_from_github(repo='clEsperanto/CLIc', branch='master')
print(f"gencle: Found {len(code_list)} tier files: {tier_list}")

# functions_list = gencle.parse_doxygen_to_json(code_list[0])
# print(f"gencle: Found {len(functions_list)} functions in tier{tier_list[0]}")
# print(functions_list[0])
# wrapper_file = gencle.generate_wrapper_file(functions_list, 1)
# python_file = gencle.generate_python_file(functions_list, 1)

for tier, code in zip(tier_list, code_list):
    print(f"gencle: Generating tier{tier} files ...")
    functions_list = gencle.parse_doxygen_to_json(code)
    print(f"gencle: \tFound {len(functions_list)} functions in tier{tier}")
    wrapper_file = gencle.generate_wrapper_file(functions_list, tier)
    python_file = gencle.generate_python_file(functions_list, tier)

    wrapper_filepath = os.path.join(WRAPPER_FOLDER, f'tier{tier}_.cpp')
    python_filepath = os.path.join(PYTHON_FOLDER, f'_tier{tier}.py')

    if gencle.write_file(wrapper_filepath, wrapper_file, overwrite=True):
        print(f"gencle: \tCreated {wrapper_filepath}")
    if gencle.write_file(python_filepath, python_file, overwrite=True):
        print(f"gencle: \tCreated {python_filepath}")