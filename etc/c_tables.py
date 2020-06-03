#!/usr/bin/env python3
import re
import glob
def precision_text(txt):
    val, total = re.sub('.timeout:.*$', '', re.sub('^.*result: ', '',txt)).split('/')
    return str(int(val) * 100.0 / int(total)) + '%'

def recall_text(txt):
    val, total = re.sub('^.*.out ', '',txt).split('/')
    return str(int(val) * 100.0 / int(total)) + '%'

def main():
    projects = ["json", "tiny", "mjs"]
    # Precision
    print("\t".join(["Precision (Table 1)", "Mimid"]))
    print('-----------------')
    for p in glob.glob('/home/vagrant/mimid/Cmimid/build/*.precision'):
        key = p.replace('/home/vagrant/mimid/Cmimid/build/','').replace('.precision', '')
        with open(p) as f:
            print(key + "\t" + precision_text(f.read().strip()))
    print()
    # fuzz
    print("\t".join(["Recall (Table 2)", "Mimid"]))
    print('-----------------')
    for p in glob.glob('/home/vagrant/mimid/Cmimid/build/*.fuzz'):
        key = p.replace('/home/vagrant/mimid/Cmimid/build/','').replace('.fuzz', '')
        with open(p) as f:
            print(key + "\t" + recall_text(f.read().strip()))

main()
