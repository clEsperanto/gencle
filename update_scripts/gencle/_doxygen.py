import re

def _parse_param_tag(line:str) -> dict:
    """Parse param tag composed of a name, type and default value.

    Parameters
    ----------
    line : str
        Line containing param tag.

    Returns
    -------
    dict
        Dictionary with parsed param tag.
    """
    # param name is the first word of the line
    tokens = line.split(maxsplit=1)
    name = tokens[0] if tokens else ''

    # get description (text between name and first brackets)
    before_bracket = line.split('[', 1)[0]
    description = before_bracket[len(name):].strip() if name else before_bracket.strip()

    # extract the string between the outermost brackets in the line (if any)
    # use rfind so inner lists such as [1, 2, 3] in default values are preserved
    info_start = line.find('[')
    info_end = line.rfind(']')
    info = line[info_start + 1:info_end] if info_start != -1 and info_end != -1 and info_end > info_start else ''

    # default value is expected as: ( = value )
    # slice until the last ')' so nested calls/lists/quotes are preserved
    default_value = ''
    default_start = re.search(r"\(\s*=", info)
    if default_start:
        default_end = info.rfind(")")
        if default_end > default_start.end():
            default_value = info[default_start.end():default_end].strip()
        else:
            default_value = info[default_start.end():].strip()

    # type is the text inside brackets, excluding optional default wrapper
    if default_start:
        param_type = info[:default_start.start()].strip()
    else:
        param_type = info.strip()
    return {'name' : name, 'type' : param_type, 'default_value' : default_value, 'description': description}


def _read_doxygen_block(block: str) -> dict:
    """Parse doxygen block. We are looking for doxygen tags specific to clesperanto:
    ['name', 'brief', 'param', 'return', 'see', 'note']

    Parameters
    ----------
    block : str
        Doxygen block.

    Returns
    -------
    dict
        Dictionary with parsed doxygen block.
    """
    # get the @name tag
    name = re.findall(r"@name\s+(.*)", block)

    # get the @priority tag
    priority = re.findall(r"@priority\s+(.*)", block)

    # get the @category tag
    category = re.findall(r"@note\s+(.*)", block)

    # get the @link tag
    link = re.findall(r"@see\s+(.*)", block)

    # get the @return tag
    return_type = re.findall(r"@return\s+(.*)", block)


    # get the @return tag
    deprecation = re.findall(r"@deprecated\s+(.*)", block)

    # get the @param tag
    params = re.findall(r"@param\s+(.*)", block)
    params_list = [_parse_param_tag(p) for p in params]

    # get the string staring with @brief and ending with @param or @return
    briefs = re.findall(r"@brief(.*?)@param", block, re.DOTALL) # [0].replace("\n *", "").strip()]
    brief = briefs[0].replace("\n *", "").strip() if len(briefs) != 0 else print(f"no brief found in {name}")
    # print(brief) if len(brief) == 0  else None

    return {'name': name[0], 'priority': priority[0] if len(priority) > 0 else '', 'category': category[0] if len(category) > 0 else '', 
            'link': link, 'return': return_type[0] if len(return_type) > 0 else '', 'parameters': params_list, 'deprecation': deprecation, 'brief': brief}


def _extract_doxygen_blocks(code: str) -> list:
    """ Extract doxygen blocks from cpp code.
    
    Notes: doxygen blocks start with `/**` and end with `*/`
    
    Parameters
    ----------
    code : str
        Code to be parsed.
        
    Returns
    -------
    list
        List of doxygen blocks.
    """
    blocks = re.findall(r"/\*\*.*?\*/", code, re.DOTALL)
    # drop the first element if it contains "@namespace"
    if blocks[0].find("@namespace") != -1:
        blocks.pop(0)
    return blocks


def parse_doxygen_to_json(code: str) -> list:
    """Parse doxygen blocks to json dict format.

    Parameters
    ----------
    code : str
        Code to be parsed.

    Returns
    -------
    list
        List of parsed doxygen blocks.
    """
    blocks = _extract_doxygen_blocks(code)
    return [_read_doxygen_block(b) for b in blocks]


def clear_doxygen_blocks(code: str) -> str:
    """Clear doxygen blocks from code.

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

