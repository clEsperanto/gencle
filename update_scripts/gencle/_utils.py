import re


def clear_doxygen_blocks(code: str) -> str:
    """Clear doxygen blocks from cpp code.

    Notes: doxygen blocks start with `/**` and end with `*/`

    Parameters
    ----------
    code : str
        Code to be cleared.

    Returns
    -------
    str
        Code without doxygen blocks.
    """
    return re.sub(r'/\*\*.*?\*/', '', code, flags=re.DOTALL)