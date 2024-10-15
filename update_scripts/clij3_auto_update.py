import gencle
import os, sys

def generate_clij_code(source_repo: str, version_tag:str) -> str:
    """
    Generate CLIJ code from the clesperantoj repo.
    
    Parameters
    ----------
    source_repo : str
        Source repository to read from.
    version_tag : str
        Version tag to read from the source repository.
    
    Returns
    -------
    str
        Generated CLIJ code.
    """

    # read tier files from clesperantoj repo
    files, tiers = gencle.read_clej_tier_from_github(
        repo=source_repo, branch=version_tag
    )
    # generate clij code from tier content
    return gencle.generate_clij_code_per_tier(files, tiers)


def update_clij_code(code: str, output_path: str) -> bool:
    """
    Update the CLIJ3.java file in the OUTPUT_REPO with the new code.
    
    Parameters
    ----------
    code : str
        New code to be updated.
    output_path : str
        Path to the OUTPUT_REPO folder.
        
    Returns
    -------
    bool
        True if the file was updated successfully, False otherwise.
    """
    # read CLIJ3.java file
    clij_file_path = os.path.join(
        output_path, "src/main/java/net/clesperanto/CLIJ3.java"
    )
    clij_class = gencle.read_file(clij_file_path)

    # update CLIJ3.java file with new code
    new_code = gencle.update_clij3_code(clij_class, code)
    return gencle.write_file(clij_file_path, new_code, overwrite=True)


def main():

    if len(sys.argv) != 3:
        print("Usage: python clij3_auto_update.py <OUTPUT_PATH> <VERSION_TAG>")
        print("Example: python clij3_auto_update.py /path/to/clesperantoj 1.2.3")
        print("This script will update the clij3 repository in the given path to version 1.2.3 of clesperantoj.")
        sys.exit(1)

    output_path = sys.argv[1]
    version_tag = sys.argv[2]
    source_repo = "clesperanto/clesperantoj_prototype"

    print("gencle: Updating CLIJ3 repo ...")
    print(f"gencle: Reading from {source_repo} at tag {version_tag}")
    print(f"gencle: Writing to {output_path}")
    code = generate_clij_code(source_repo, version_tag)
    update_clij_code(code, output_path)
    print("gencle: Done!")


if __name__ == "__main__":
    main()
