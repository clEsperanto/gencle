import gencle
import os, sys

OUTPUT_REPO = sys.argv[1]
VERSION_TAG = sys.argv[2]
SOURCE_REPO = "clesperanto/clesperantoj_prototype"
OUTPUT_REPO = "/Users/strigaud/Documents/github/clesperanto/clij3"


def main():

    # read tier files from clesperantoj repo
    files, tiers = gencle.read_clej_tier_from_github(
        repo=SOURCE_REPO, branch=VERSION_TAG
    )

    # generate clij code from tier content
    clij_code = gencle.generate_clij_code_per_tier(files, tiers)

    # read CLIJ3.java file
    clij_file_path = os.path.join(
        OUTPUT_REPO, "src/main/java/net/clesperanto/CLIJ3.java"
    )
    clij_class = gencle.read_file(clij_file_path)

    # update CLIJ3.java file with new code
    new_clij_class = gencle.update_clij3_code(clij_class, clij_code)

    print(new_clij_class)

    # write new CLIJ3.java file
    gencle.write_file(clij_file_path, new_clij_class, overwrite=True)


if __name__ == "__main__":
    main()
