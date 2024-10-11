import gencle
import os, sys

OUTPUT_REPO = sys.argv[1]  # clij3 repo
VERSION_TAG = sys.argv[2]  # clesperantoj version tag
SOURCE_REPO = "clesperanto/clesperantoj_prototype"
# OUTPUT_REPO = "/Users/strigaud/Documents/github/clesperanto/clij3"


def generate_clij_code() -> str:
    # read tier files from clesperantoj repo
    files, tiers = gencle.read_clej_tier_from_github(
        repo=SOURCE_REPO, branch=VERSION_TAG
    )
    # generate clij code from tier content
    return gencle.generate_clij_code_per_tier(files, tiers)


def update_clij_code(code: str) -> bool:
    # read CLIJ3.java file
    clij_file_path = os.path.join(
        OUTPUT_REPO, "src/main/java/net/clesperanto/CLIJ3.java"
    )
    clij_class = gencle.read_file(clij_file_path)

    # update CLIJ3.java file with new code
    new_code = gencle.update_clij3_code(clij_class, code)
    return gencle.write_file(clij_file_path, new_code, overwrite=True)


def main():

    code = generate_clij_code()
    update_clij_code(code)


if __name__ == "__main__":
    main()
