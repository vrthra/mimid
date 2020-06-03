#!/usr/bin/env python3
import re
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
    for key in projects:
        with open("/home/vagrant/mimid/Cmimid/build/%s.precision" % key) as f:
            print(key + "\t" + precision_text(f.read().strip()))
    print()
    # fuzz
    print("\t".join(["Recall (Table 2)", "Mimid"]))
    print('-----------------')
    for key in projects:
        with open("/home/vagrant/mimid/Cmimid/build/%s.fuzz" % key) as f:
            print(key + "\t" + recall_text(f.read().strip()))

main()
