"""Takes a file containing PanOS curly braces and outputs it to terminal in CSV or JSON format.

usage: palo_showrun_converter.py [-h] [-s CSV_SEP] [-j] input_file
"""
import re
import csv
import json
import sys
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Takes a file containing PanOS output of '
                                                 'operational commands with curly braces, such as '
                                                 '"show running security-policy", and outputs it to'
                                                 ' terminal in CSV or JSON format. It also breaks'
                                                 ' up multi-entry fields (e.g. a policy with '
                                                 'multiple destination addresses enclosed in square'
                                                 ' brackets) and turns them into actual JSON lists '
                                                 'and multi-line CSV fields, prepending a "!" when'
                                                 ' the field has the Negate option selected.')
    parser.add_argument('input_file', type=str, help='Text file containing the command output')
    parser.add_argument('-s', '--csv-sep', type=str, default=',', help='CSV separator. Default: ,')
    parser.add_argument('-j', '--json', action='store_true', help='Output JSON instead of CSV')
    args = parser.parse_args()
    brace_level = 0
    csv_list = []
    keys = ['title']
    with open(args.input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if brace_level == 1:
                line = line.strip()
                try:
                    if line[-1] == '}':
                        brace_level = 0
                        csv_list.append(csv_row_dict)
                        continue
                except IndexError:
                    continue
                result = re.search(r'^(\S+)(.*);$', line)
                if not result:
                    continue
                column_title = result.group(1)
                column_content = result.group(2).strip()
                negate = ''
                # Add "!" before negated addresses
                if column_content.endswith('(negate)'):
                    negate = '!'
                    column_content = column_content[:-len('(negate)')]
                # Split "[  ]" into actual lists
                if column_content[0] == '[' and column_content[-1] == ']':
                    column_content = column_content.replace('[', '').replace(']', '').split()
                    column_content = [negate + f for f in column_content]
                    if not args.json:
                        content_string = ''
                        for g in column_content:
                            content_string += g + '\n'
                        column_content = content_string.strip()
                else:
                    column_content = negate + column_content
                csv_row_dict[column_title] = column_content
                if column_title not in keys:
                    keys.append(column_title)
            if brace_level == 0:
                try:
                    if line[-2] == '{':
                        brace_level = 1
                        csv_row_dict = {}
                        result = re.search(r'^(.*) \{$', line)
                        if not result:
                            result = 'N/A'
                        csv_row_dict['title'] = result.group(1).replace('"', '')
                        continue
                except IndexError:
                    continue
    if args.json:
        print(json.dumps(csv_list))
    else:
        dict_writer = csv.DictWriter(sys.stdout, keys, delimiter=args.csv_sep,
                                     quoting=csv.QUOTE_ALL)
        dict_writer.writeheader()
        dict_writer.writerows(csv_list)
