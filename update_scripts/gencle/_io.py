import os, glob, json
import urllib.request

from typing import List, Tuple

def read_tier_from_github(repo: str = 'clEsperanto/CLIc', branch: str ='master') -> Tuple[List[str], List[int]]:
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
        file_path = f'clic/include/tier{tier}.hpp'
        raw_file_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{file_path}"

        try:
            with urllib.request.urlopen(raw_file_url) as response:
                if response.status == 200:
                    code_list.append(response.read().decode('utf-8'))
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
    tier_list =  glob.glob(os.path.join(folder, '**', 'tier*.hpp'), recursive=True)
    tier_list = [t for t in tier_list if 'tier0' not in t]
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
        with open(filepath, 'r') as file:
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
        with open(filepath, 'w') as file:
            json.dump(json_data, file, indent=4)
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return None
    
    
def write_file(filepath: str, content: str, create_folder: bool =True, overwrite: bool =False) -> bool:
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
        backup_filepath = filepath + '.backup'
        os.rename(filepath, backup_filepath)
    
    try:
        with open(filepath, 'w') as file:
            file.write(content)
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return False
    return True