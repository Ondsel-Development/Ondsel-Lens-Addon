import re


# source: https://chatgpt.com/  after a cleaned it up a bit
def markdown_to_html(markdown_text):
    # Convert headers (supporting up to 6 levels)
    markdown_text = re.sub(r"###### (.*)", r"<h6>\1</h6>", markdown_text)
    markdown_text = re.sub(r"##### (.*)", r"<h5>\1</h5>", markdown_text)
    markdown_text = re.sub(r"#### (.*)", r"<h4>\1</h4>", markdown_text)
    markdown_text = re.sub(r"### (.*)", r"<h3>\1</h3>", markdown_text)
    markdown_text = re.sub(r"## (.*)", r"<h2>\1</h2>", markdown_text)
    markdown_text = re.sub(r"# (.*)", r"<h1>\1</h1>", markdown_text)

    # Convert bold (**text** or __text__)
    markdown_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", markdown_text)
    markdown_text = re.sub(r"__(.*?)__", r"<strong>\1</strong>", markdown_text)

    # Convert italics (*text* or _text_)
    markdown_text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", markdown_text)
    markdown_text = re.sub(r"_(.*?)_", r"<em>\1</em>", markdown_text)

    # Convert links [text](url)
    markdown_text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', markdown_text)

    # Convert bulleted lists
    lines = markdown_text.split("\n")
    in_list = False
    html_lines = []
    paragraph_buffer = []

    for line in lines:
        line = line.strip()  # Remove leading and trailing spaces
        if re.match(r"^[*-] ", line):
            if paragraph_buffer:
                html_lines.append(f'<p>{" ".join(paragraph_buffer)}</p>')
                paragraph_buffer = []
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{line[2:]}</li>")
        elif line:  # Any non-empty line (could be paragraph or header)
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            paragraph_buffer.append(line)
        else:  # Empty line signals the end of a paragraph
            if paragraph_buffer:
                html_lines.append(f'<p>{" ".join(paragraph_buffer)}</p>')
                paragraph_buffer = []
            if in_list:
                html_lines.append("</ul>")
                in_list = False

    # Close any remaining open paragraph or list
    if paragraph_buffer:
        html_lines.append(f'<p>{" ".join(paragraph_buffer)}</p>')
    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)
