import gencle
import os, sys

# OUTPUT_REPO = sys.argv[1]
# VERSION_TAG = sys.argv[2]
# SOURCE_REPO = "clEsperanto/CLIc"


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
    code_list, tier_list = gencle.read_clic_tier_from_github(repo=src_repo, branch=tag)
    for tier, code in zip(tier_list, code_list):
        functions_list = gencle.parse_doxygen_to_json(code)
        wrapper_file = gencle.generate_wrapper_file(functions_list, tier)
        python_file = gencle.generate_python_file(functions_list, tier)
        wrapper_filepath = os.path.join(
            os.path.join(dst_repo, "src/wrapper"), f"tier{tier}_.cpp"
        )
        python_filepath = os.path.join(
            os.path.join(dst_repo, "pyclesperanto"), f"_tier{tier}.py"
        )
        gencle.write_file(wrapper_filepath, wrapper_file, overwrite=True)
        gencle.write_file(python_filepath, python_file, overwrite=True)


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

    version_file = os.path.join(os.path.join(dst_repo, "pyclesperanto"), "_version.py")

    # if file does not exist, return
    if not os.path.exists(version_file):
        print(f"gencle: Fail updating CLIc version. Could not find {version_file}")
        return

    with open(version_file, "r") as file:
        data = file.readlines()
    for i, line in enumerate(data):
        if "CLIC_VERSION =" in line:
            data[i] = f'CLIC_VERSION = "{tag}"\n'
            break
    with open(version_file, "w") as file:
        file.writelines(data)


def main():
    if len(sys.argv) != 3:
        print("Usage: python pyclesperanto_auto_update.py <OUTPUT_PATH> <VERSION_TAG>")
        print("Example: python pyclesperanto_auto_update.py /path/to/clesperantoj 1.2.3")
        print("This script will update the pyclesperanto repository in the given path to version 1.2.3 of CLIc.")
        sys.exit(1)

    output_path = sys.argv[1]
    version_tag = sys.argv[2]
    source_repo = "clEsperanto/CLIc"

    print("gencle: Updating pyclesperanto repo ...")
    print(f"gencle: Reading from {source_repo} at tag {version_tag}")
    print(f"gencle: Writing to {output_path}")
    update_tier_code(output_path, source_repo, version_tag)
    update_version_file(output_path, version_tag)
    print("gencle: Done!")


if __name__ == "__main__":
    main()
