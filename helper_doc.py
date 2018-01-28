#!/usr/env/python2.7

import os
import glob

def render(data):

    import datetime
    from jinja2 import Template
    from ansi2html import Ansi2HTMLConverter
    from ansi2html.style import get_styles

    conv = Ansi2HTMLConverter()
    shell_css = "\n".join(map(str, get_styles(conv.dark_bg, conv.scheme)))

    def shell_to_html(shell):
        return conv.convert(shell, False)

    template = open("helper_template.html", "r").read()
    t        = Template(template)
    t.globals['now'] = datetime.datetime.utcnow
    result = t.render(data=data, convert=shell_to_html, shell_css=shell_css)
    open("index.html", "w").write(result)

##############################################################################

class Parser():

    def __init__(self, filename):

        self.file = open(filename, "r").readlines()
        self.blocks = None

    def parse_blocks(self):

        self.blocks = []

        current_reading = "void"
        current_block = { "name": None,
                          "line": -1,
                          "comments": [],
                          "code": [] }

        for i, line in enumerate(self.file):

            line = line.rstrip().replace("\t", "    ")

            if current_reading == "void":
                if is_global_comment(line):
                    # We start a new comment bloc
                    current_reading = "comments"
                    assert line.startswith("# ") or line == "#", malformed_error(i)
                    current_block["comments"].append(line[2:])
                else:
                    pass
                    #assert line == "", malformed_error(i)
                continue

            elif current_reading == "comments":
                if is_global_comment(line):
                    # We're still in a comment bloc
                    assert line.startswith("# ") or line == "#", malformed_error(i)
                    current_block["comments"].append(line[2:])
                else:
                    # We're getting out of a comment bloc, we should find
                    # the name of the function
                    assert len(line.split()) >= 1
                    current_block["line"] = i
                    current_block["name"] = line.split()[0].strip("(){")
                    # Then we expect to read the function
                    current_reading = "code"

                continue

            elif current_reading == "code":

                if line == "}":
                    # We're getting out of the function
                    current_reading = "void"

                    # Then we keep this bloc and start a new one
                    self.blocks.append(current_block)
                    current_block = { "name": None,
                                      "line": -1,
                                      "comments": [],
                                      "code": [] }
                else:
                    current_block["code"].append(line)
                    pass

                continue

    def parse_block(self, b):

        b["brief"] = ""
        b["details"] = ""
        b["usage"] = ""
        b["args"] = []
        b["ret"] = ""
        b["example"] = ""

        subblocks = '\n'.join(b["comments"]).split("\n\n")

        for i, subblock in enumerate(subblocks):
            subblock = subblock.strip()

            if i == 0:
                b["brief"] = subblock
                continue

            elif subblock.startswith("example"):
                b["example"] = " ".join(subblock.split()[1:])
                continue

            elif subblock.startswith("usage"):
                for line in subblock.split("\n"):

                    if line.startswith("| arg"):
                        argname = line.split()[2]
                        argdescr = " ".join(line.split()[4:])
                        b["args"].append((argname, argdescr))
                    elif line.startswith("| ret"):
                        b["ret"] = " ".join(line.split()[2:])
                    else:
                        if line.startswith("usage"):
                            line = " ".join(line.split()[1:])
                        b["usage"] += line + "\n"
                continue

            elif subblock.startswith("| arg"):
                for line in subblock.split("\n"):
                    if line.startswith("| arg"):
                        argname = line.split()[2]
                        argdescr = line.split()[4:]
                        b["args"].append((argname, argdescr))
                continue

            else:
                b["details"] += subblock + "\n\n"

        b["usage"] = b["usage"].strip()


def is_global_comment(line):
    return line.startswith('#')

def malformed_error(line_number):
    return "Malformed file line {} ?".format(line_number)

def main():

    helper_files = glob.glob("./yunohost/data/helpers.d/*")
    helpers = {}

    for helper_file in helper_files:
        category_name = os.path.basename(helper_file)
        print "Parsing %s ..." % category_name
        p = Parser(helper_file)
        p.parse_blocks()
        for b in p.blocks:
            p.parse_block(b)

        helpers[category_name] = p.blocks

    render(helpers)

main()

