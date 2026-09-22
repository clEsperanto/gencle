import glob
import json
import os
import re
import urllib.request

from typing import Dict, List, Tuple


# Namespaces in CLIc that do not follow the "tierN" naming convention but are
# still wrapped as their own named class in clesperantoj (see kernelj.hpp).
# This is the built-in fallback used when the destination repository does not
# ship its own override file (see `read_class_overrides_config`).
DEFAULT_NAMESPACE_CLASS_OVERRIDES: Dict[str, str] = {
    "fft": "FFT",
    "transform": "Transform",
}

# Relative path, inside the destination (e.g. clesperantoj) repository, where a
# custom class-override/allowlist file can be placed to extend or replace
# DEFAULT_NAMESPACE_CLASS_OVERRIDES without requiring a change in gencle itself.
CLASS_OVERRIDES_CONFIG_PATH = os.path.join(
    "native", "clesperantoj", "include", "class_overrides.json"
)


def read_class_overrides_config(dst_repo: str) -> Dict[str, object]:
    """Read the namespace-to-class override/allowlist configuration.

    This lets a destination repository (e.g. clesperantoj) declare that a
    given CLIc namespace (e.g. ``fft``) should keep being generated as a
    custom named class (e.g. ``FFT``) instead of being merged into whichever
    ``TierN`` it happens to live under, and which top-level classes must be
    treated as protected (i.e. never silently dropped) during regeneration.

    The configuration file is optional. When absent, a built-in default
    (`DEFAULT_NAMESPACE_CLASS_OVERRIDES`) is used.

    Expected JSON schema::

        {
            "namespace_class_overrides": {"fft": "FFT", "transform": "Transform"},
            "allowed_removals": []
        }

    Parameters
    ----------
    dst_repo : str
        Path to the destination repository folder (e.g. clesperantoj).

    Returns
    -------
    dict
        Dictionary with keys ``namespace_class_overrides`` (dict[str, str])
        and ``allowed_removals`` (list[str]).
    """
    config_filepath = os.path.join(dst_repo, CLASS_OVERRIDES_CONFIG_PATH)

    namespace_class_overrides = dict(DEFAULT_NAMESPACE_CLASS_OVERRIDES)
    allowed_removals = []

    if os.path.exists(config_filepath):
        try:
            with open(config_filepath, "r") as file:
                data = json.load(file)
            namespace_class_overrides.update(
                data.get("namespace_class_overrides", {})
            )
            allowed_removals = data.get("allowed_removals", [])
        except (json.JSONDecodeError, OSError) as error:
            print(
                f"gencle: Could not read class overrides config at {config_filepath}: {error}"
            )

    return {
        "namespace_class_overrides": namespace_class_overrides,
        "allowed_removals": allowed_removals,
    }


def list_declared_classes(header_content: str) -> List[str]:
    """List the names of all top-level classes declared in a kernelj.hpp-like header.

    Parameters
    ----------
    header_content : str
        Contents of the header file.

    Returns
    -------
    list of str
        Names of the declared classes, in order of appearance.
    """
    if not header_content:
        return []
    return re.findall(r"^\s*class\s+(\w+)", header_content, flags=re.MULTILINE)


def extract_class_block(header_content: str, class_name: str) -> str:
    """Extract the full ``class Name { ... };`` declaration block from a header.

    Parameters
    ----------
    header_content : str
        Contents of the header file to search in.
    class_name : str
        Name of the class to extract.

    Returns
    -------
    str or None
        The full class declaration block (including trailing semicolon), or
        None if the class could not be found.
    """
    if not header_content:
        return None
    pattern = re.compile(
        r"class\s+" + re.escape(class_name) + r"\s*\{.*?\}\s*;", re.DOTALL
    )
    match = pattern.search(header_content)
    if not match:
        return None
    return match.group(0)


def read_clej_tier_from_github(
    repo: str = "clEsperanto/clesperantoj", branch: str = "master"
) -> Tuple[List[str], List[int]]:
    """Read tier file from github repository.

    Notes: small update time is required after a push to github to get the latest version.

    Parameters
    ----------
    tier : int
        Tier file (number) to read.
    repo : str, optional
        Repository to read from, by default 'clEsperanto/CLIc_prototype'.
    branch : str, optional
        Branch to read from, by default 'master'.

    Returns
    -------
    str
        Contents of tier file.
    """

    tier_list = []
    code_list = []
    for tier in range(1, 10):
        file_path = f"src/main/java/net/clesperanto/kernels/Tier{tier}.java"
        raw_file_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{file_path}"

        try:
            with urllib.request.urlopen(raw_file_url) as response:
                if response.status == 200:
                    code_list.append(response.read().decode("utf-8"))
                    tier_list.append(tier)
                else:
                    break
        except urllib.error.URLError:
            break

    return code_list, tier_list


def read_clic_tier_from_github(
    repo: str = "clEsperanto/CLIc", branch: str = "master"
) -> Tuple[List[str], List[int]]:
    """Read tier file from github repository.

    Notes: small update time is required after a push to github to get the latest version.

    Parameters
    ----------
    tier : int
        Tier file (number) to read.
    repo : str, optional
        Repository to read from, by default 'clEsperanto/CLIc_prototype'.
    branch : str, optional
        Branch to read from, by default 'master'.

    Returns
    -------
    str
        Contents of tier file.
    """

    tier_list = []
    code_list = []
    for tier in range(1, 10):
        file_path = f"clic/include/tier{tier}.hpp"
        raw_file_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{file_path}"

        try:
            with urllib.request.urlopen(raw_file_url) as response:
                if response.status == 200:
                    code_list.append(response.read().decode("utf-8"))
                    tier_list.append(tier)
                else:
                    break
        except urllib.error.URLError:
            break

    return code_list, tier_list


def list_tier_files(folder: str) -> list:
    """List all tier files in CLIc folder.

    Parameters
    ----------
    folder : str
        Path to CLIc folder.

    Returns
    -------
    list
        List of tier files.
    """
    # find recusively all files in folder and subfolders fitting the pattern 'tier*.hpp'
    tier_list = glob.glob(os.path.join(folder, "**", "tier*.hpp"), recursive=True)
    tier_list = [t for t in tier_list if "tier0" not in t]
    return tier_list


def read_file(filepath: str) -> str:
    """Read file.

    Parameters
    ----------
    filepath : str
        Path to tier file.

    Returns
    -------
    str
        Contents of tier file.
    """
    try:
        with open(filepath, "r") as file:
            content = file.read()
        return content
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return None


def write_json_file(filepath: str, json_data: dict) -> None:
    """Write json file.

    Parameters
    ----------
    filepath : str
        Path to json file.
    json_data : dict
        Data to be written.
    """
    try:
        with open(filepath, "w") as file:
            json.dump(json_data, file, indent=4)
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return None


def _normalize_content(content: str) -> str:
    """Normalize generated content to satisfy common pre-commit hooks.

    Strips trailing whitespace from every line (trailing-whitespace hook)
    and ensures the file ends with exactly one newline (end-of-file-fixer hook).

    Parameters
    ----------
    content : str
        Content to normalize.

    Returns
    -------
    str
        Normalized content.
    """
    lines = [line.rstrip() for line in content.splitlines()]
    return "\n".join(lines).strip("\n") + "\n"


def write_file(
    filepath: str, content: str, create_folder: bool = True, overwrite: bool = False
) -> bool:
    """Write file.

    Parameters
    ----------
    filepath : str
        Path to file.
    content : str
        Content to be written.
    """
    if create_folder and not os.path.exists(os.path.dirname(filepath)):
        os.makedirs(os.path.dirname(filepath))

    # if file already exists, save a backup copy first
    if not overwrite and os.path.exists(filepath):
        backup_filepath = filepath + ".backup"
        os.rename(filepath, backup_filepath)

    content = _normalize_content(content)

    try:
        with open(filepath, "w") as file:
            file.write(content)
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return False
    return True
