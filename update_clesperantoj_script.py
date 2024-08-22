import gencle
import os

# manage folder paths
CLEJ_FOLDER = '/data/clesperanto/clesperantoj_prototype'
HEADER_FOLDER = os.path.join(CLEJ_FOLDER, 'native/clesperantoj/include')
SOURCE_FOLDER = os.path.join(CLEJ_FOLDER, 'native/clesperantoj/src')
JAVA_FOLDER = os.path.join(CLEJ_FOLDER, 'src/main/java/net/clesperanto/kernels')

code_list, tier_list = gencle.read_tier_from_github(repo='clEsperanto/CLIc', branch='master')
print(f"gencle: Found {len(code_list)} tier files: {tier_list}")

header_file = []
for tier, code in zip(tier_list, code_list):
    functions_list = gencle.parse_doxygen_to_json(code)
    header, code = gencle.generate_native_tier_code(tier, functions_list)
    source_filepath = os.path.join(SOURCE_FOLDER, f'tier{tier}j.cpp')
    gencle.write_file(source_filepath, code, overwrite=True )
    header_file.append(header)
header_filepath = os.path.join(HEADER_FOLDER, f'kernelj.hpp')
gencle.write_file(header_filepath, code, overwrite=True )


for tier, code in zip(tier_list, code_list):
    functions_list = gencle.parse_doxygen_to_json(code)
    java_tier = gencle.generate_java_class(tier, functions_list)
    java_filepath = os.path.join(JAVA_FOLDER, f'Tier{tier}.java')
    gencle.write_file(java_filepath, code, overwrite=True )