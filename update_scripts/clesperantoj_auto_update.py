import gencle
import os, sys

def update_tier_code(dst_repo: str, src_repo: str, tag: str):
    """
    Update the tier code in the OUTPUT_REPO by reading the tier files from the SOURCE_REPO

    Parameters
    ----------
    dst_repo : str
        Path to the OUTPUT_REPO folder.
    src_repo : str
        Path to the SOURCE_REPO folder.
    tag : str
        Version tag to be used in the OUTPUT_REPO.

    Returns
    -------
        None
    """

    java_folder = os.path.join(dst_repo, "src/main/java/net/clesperanto/kernels")
    source_folder = os.path.join(dst_repo, "native/clesperantoj/src")
    header_folder = os.path.join(dst_repo, "native/clesperantoj/include")

    code_list, tier_list = gencle.read_clic_tier_from_github(repo=src_repo, branch=tag)
    header_file = []
    for tier, code in zip(tier_list, code_list):
        functions_list = gencle.parse_doxygen_to_json(code)
        header, code = gencle.generate_native_tier_code(tier, functions_list)
        source_filepath = os.path.join(source_folder, f"tier{tier}j.cpp")
        gencle.write_file(source_filepath, code, overwrite=True)
        header_file.append(header)
    header_filepath = os.path.join(header_folder, f"kernelj.hpp")
    gencle.write_file(header_filepath, code, overwrite=True)

    for tier, code in zip(tier_list, code_list):
        functions_list = gencle.parse_doxygen_to_json(code)
        java_tier = gencle.generate_java_class(tier, functions_list)
        java_filepath = os.path.join(java_folder, f"Tier{tier}.java")
        gencle.write_file(java_filepath, java_tier, overwrite=True)


def update_version_file(dst_repo: str, tag: str):
    """
    Update the CLIc version tag.

    Parameters
    ----------
    dst_repo : str
        Path to the OUTPUT_REPO folder.
    tag : str
        Version tag to be used in the OUTPUT_REPO.

    Returns
    -------
        None
    """

    cmake_file = os.path.join(
        os.path.join(dst_repo, "native/clesperantoj"), "CMakeLists.txt"
    )
    # pom_file = os.path.join(dst_repo,'pom.xml')

    if not os.path.exists(cmake_file):
        print(f"gencle: Fail updating CLIc version. Could not find {cmake_file}")
        return

    with open(cmake_file, "r") as file:
        data = file.readlines()
    for i, line in enumerate(data):
        if "set(CLIC_REPO_TAG" in line:
            data[i] = f"set(CLIC_REPO_TAG {tag})\n"
            break
    with open(cmake_file, "w") as file:
        file.writelines(data)


def main():
    if len(sys.argv) != 3:
        print("Usage: python clesperantoj_auto_update.py <OUTPUT_PATH> <VERSION_TAG>")
        print("Example: python clesperantoj_auto_update.py /path/to/clesperantoj 1.2.3")
        print("This script will update the clesperantoj repository in the given path to version 1.2.3 of CLIc.")
        sys.exit(1)

    output_path = sys.argv[1]
    version_tag = sys.argv[2]
    source_repo = "clEsperanto/CLIc"

    print("gencle: Updating clesperantoj repo ...")
    print(f"gencle: Reading from {source_repo} at tag {version_tag}")
    print(f"gencle: Writing to {output_path}")
    update_tier_code(output_path, source_repo, version_tag)
    update_version_file(output_path, version_tag)
    print("gencle: Done!")


if __name__ == "__main__":
    main()
