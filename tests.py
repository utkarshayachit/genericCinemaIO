"""
This module tests cinemaDB.
"""

from cinemaDB import *

def test_read(fname = None, silent = True):
    if not fname:
        fname = "info.json"
    cs = cinema_store(fname)
    if not cs.verify():
        print "problem with that file"
        return None

    if not silent:
        print "CS", cs
        print "ARGS", cs.get_arguments()
        print "NPS", cs.get_name_pattern_string()
        print "MD", cs.get_metadata()
    return cs

def test_argument(fname = None):
    cs = test_read(fname, True)

    if not cs:
        return

    print "* before"
    args = cs.get_arguments()
    for x in args:
        print x, "\t", args[x]

    a = cs.add_argument("theta", [0,45,90,135,180])

    print "* after"
    args = cs.get_arguments()
    for x in args:
        print x, "\t", args[x]

def test_name_pattern():
    cs = cinema_store("info.json")
    cs.set_name_pattern("time","theta","range")
    print(cs.get_name_pattern_string())
    cs.set_name_pattern("theta","time","range",usedir=True)
    print(cs.get_name_pattern_string())
    cs.set_name_pattern("theta","time","range",usedir=False)
    print(cs.get_name_pattern_string())

def test_write(fname=None):
    if not fname:
        fname = "info.json"
    cs = cinema_store(fname)

    cs.set_metadata = {"testing":123}
    a = cs.add_argument("theta", [0,45,90,135,180])
    a = cs.add_argument("filename", ["rgb.png"], typechoice='list')
    cs.misc_json["miscelaneous"] = "vilanous"
    cs.set_name_pattern_string("{theta}")
    cs.write_json(fname)
    return cs

def test_load_item(fname = None):
    def handler(fullname,arguments):
        import hashlib
        import os
        if not os.path.exists(fullname):
            print fullname, "is missing"
        else:
            print fullname, hashlib.md5(open(fullname, 'rb').read()).hexdigest()
    cs = test_read(fname)
    res = cs.load_item({'phi':120,'time':10,'filename':'nada.txt'}, handler)
    res = cs.load_item({'phi':120,'time':10,'filename':'rgb.png'}, handler)

def test_save_item(fname = None):
    def handler(fullname, item, arguments):
        fd = open(fullname, 'w')
        fd.write(item)
        fd.close()
    cs = test_read(fname)
    res = cs.save_item({'phi':120,'time':10,'filename':'event.txt'},
                       "The quick brown fox jumped over the lazy dog.\n", handler)

def test_next(fname=None):
    def handler(fullname, arguments):
        print fullname, arguments

    cs = test_read(fname)
    cs.add_argument("phi", [0,45,90,135,180])
    cs.set_name_pattern("theta","phi")

    for args, idx in cs.next_set():
        cs.load_item(args, handler)

def demontrate_populate(fname="info.json"):
    cs = cinema_store(fname)
    cs.set_name_pattern_string("{theta}/{phi}")
    cs.add_argument("theta", [0,10,20,30,40])
    cs.add_argument("phi", [0,10,20,30,40])
    cs.write_json()

    import shutil

    def handler(fullname, ifile, arguments):
        print "cp", ifile, fullname
        shutil.copyfile(ifile, fullname)

    for args, idx in cs.next_set():
        ifile = "/Users/demarle/tmp/infiles/file_" + str(idx) + ".txt"
        args['filename']="copy2"
        cs.save_item(args, ifile, handler)

def demonatrate_analyze(fname="info.json"):
    cs = cinema_store(fname)

    def handler(fullname, arguments):
        print fullname
        fd = open(fullname, 'r')
        for line in fd:
            print line
        fd.close()

    for args, idx in cs.next_set():
        args['filename']="copy2"
        cs.load_item(args, handler)

if __name__ == "__main__":
    None
