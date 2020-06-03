#!/usr/bin/env python3

def extract(lines):
    results = []
    add = False
    for line in lines:
        if line.startswith('<h2 id="Results">'):
            add = True
        elif line.startswith('<h2 id="'):
            add = False
        else:
            if add:
                results.append(line)
    return results


def extract_tables(lines):
    all_tables = []
    cur_table = []
    for line in lines:
        if line.startswith('<h3 id='):
            if cur_table:
                all_tables.append(cur_table)
            cur_table = []
        cur_table.append(line)
    all_tables.append(cur_table)
    return all_tables

def strip_trtd(line):
    return line.replace('<tr><td>', '').replace('</td></tr>', '').replace('<td>', '').replace('</td>', ',').strip().split(',')

def header(line):
    return re.sub('</b>.*','', line.strip().replace('<table><tr><th><b>', ''))

def to_values(lines):
    result = []
    add = False
    for line in lines:
        if line.startswith('<table>'):
            add = True
            h = header(line)
        elif line.strip().endswith('</table>'):
            add = False
        else:
            if add:
                result.append(strip_trtd(line))

    return h, result

def main(fn):
    with open(fn) as f:
        lines = f.readlines()
    tables = extract(lines)
    _,table1, table2, table3 = extract_tables(tables)
    # Timing
    #header, values = to_values(table1)
    #print("\t".join([header, "Autogram", "Mimid"]))
    #print("-----------------")
    #for line in values:
    #    print(',\t'.join(line))
    #print()
    # Precision
    header, values = to_values(table2)
    print("\t".join([header + " (Table 1)", "Autogram", "Mimid"]))
    print("-----------------")
    for line in values:
        print(',\t'.join(line))
    print()
    # Recall
    header, values = to_values(table3)
    print("\t".join([header + " (Table 2)", "Autogram", "Mimid"]))
    print("-----------------")
    for line in values:
        print(',\t'.join(line))


import sys, re
#main(sys.argv[1])
main('/home/vagrant/PymimidBook.html')

