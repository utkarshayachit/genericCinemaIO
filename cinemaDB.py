"""
This module defines a structured API to working with cinema data stores.
"""

#TODO:
#children
#deal with cases where we want less than or more than one file cleanly
#extensions for specific cinema types that need to work on metadata
#bring over seb's and scott's scripts on top of this
#todo: cleanup terms 'args', 'item', and 'each'

import sys
import json
import os.path
import re
import itertools

class CinemaStore :
    """
    A class to represent a set of data that cinema works with.
    Basic things this does for you are:
    * get a handle on a directory containing a cinema data store
    * traverse parent child hiearchy (workbench type store of stores)
    * search for, add and remove items
    * write out the contents into a directory
    """

    def __init__(self, filename):
        self._filename = filename
        self.json = None

        self._arguments = None #better name is parameters
        self._name_pattern = None #better name is file_mapping
        self._metadata = None #better name is view hints
        self._active_arguments = {}
        self.misc_json = {}
        self.read_json(dontcare=True)

    @staticmethod
    def fromArguments(arguments, filename='info.json', metadata=None):
        """
        construct a CinemaStore from an argument list
        each argument in the list consists of a two or three element list containing:
        a name, a list of values and optional specs
        the optionals, specified inside a {} dict are:
            'typechoice'= default is 'range'
            'label'= default is name
            'default'= default is values[0]
        """
        cs = CinemaStore(filename)
        np = ""
        for x in arguments:
            #todo: better args handling to make the uncommon options easier to use
            if len(x) == 3:
                a = cs.add_argument(x[0], x[1], **x[2])
            else:
                a = cs.add_argument(x[0], x[1])
            aname = "{" + x[0] + "}"
            if not np:
                np = aname
            else:
                np += "/" + aname;
        cs.set_name_pattern_string(np)
        return cs

    def read_json(self, dontcare=False):
        try:
            fd = open(self._filename, 'r')
        except IOError:
            if dontcare:
                return
            else:
                raise
        self.json = json.load(fd)
        self._arguments = self.json[u'arguments']
        self.set_name_pattern_string(self.json[u'name_pattern'])
        self.set_metadata(self.json[u'metadata'])
        self.misc_json = {}
        for x in self.json:
            if x not in [u'arguments', u'name_pattern', u'metadata']:
                self.misc_json[x] = self.json[x]
        fd.close()

    def write_json(self, filename=None):
        if not self.verify():
            print "error, not ready to write yet"
            return
        
        if filename:
            self._filename = filename
        fd = open(self._filename, 'w') #let python fail for now instead of catch
        self.json = dict(
            arguments=self._arguments,
            name_pattern=self.get_name_pattern_string(),
            metadata=self._metadata
            )
        self.json.update(self.misc_json)
        json.dump(self.json, fd)
        fd.close()

    def get_directory(self):
        return os.path.dirname(os.path.realpath(self._filename))

    def verify(self):
        failed = True
        try:
            if self._arguments and self._name_pattern: # and self._metadata:
                #TODO, check the contents for any other semantics we care about too
                failed = False
        finally:
            if failed:
                return False
            else:
                return True

    def get_children(self):
        """
        Returns None or the immediate children of this cinema store.
        For working with workbench collections.
        #ideally this will boil down to a getItem call
        """
        print "TODO"
        return None

    def add_child(self, child):
        """
        #ideally this will boil down to a setItem call
        """
        print "TODO"
        return None

    def get_metadata(self):
        """
        access to the metadata section
        """
        return self._metadata

    def set_metadata(self, metadata):
        """
        overwrite the metadata section
        """
        self._metadata = metadata
        #TODO: hooks for type specific customizations can go here

    def get_arguments(self):
        """
        returns 'arguments' the parameter set that the results
        range over. """
        return self._arguments

    def get_argument(self, name):
        """
        returns 'arguments' the parameter set that the results
        range over. """
        return self.get_arguments()[name]

    def add_argument(self, name, values, **kwargs):
        """ adds a new argument to the list """
        ##todo, if caller has not set name_pattern, make it up a we add arguments

        typechoice = 'range'
        if 'typechoice' in kwargs:
            typechoice = kwargs['typechoice']
        default = None
        if 'default' in kwargs:
            default = kwargs['default']
        label = None
        if 'label' in kwargs:
            label = kwargs['label']

        a = CinemaStore._make_argument(name, values, typechoice, default, label)
        if a:
            if not self._arguments:
                self._arguments = {}
            #check if already present or just replace?
            self._arguments[name] = a
        return a

    @staticmethod
    def _make_argument(name, values, typechoice, default = None, label = None):
        types = ['list','range']
        if not typechoice in types:
            print "invalid typechoice, must be on of ", types
            return None
        if not default:
            default = values[0]
        if not default in values:
            print "invalid default, must be one of", values
            return None
        if not label:
            label = name
        argument = dict()
        argument['type'] = typechoice
        argument['label'] = label
        argument['values'] = values
        argument['default'] = default
        return argument

    def get_name_pattern_string(self):
        if not self._name_pattern:
            return None
        usedir = False;
        if self._name_pattern['usedir'] == True:
            usedir = True
        res = "{" + self._name_pattern['args'][0] + "}"
        for a in range(1,len(self._name_pattern['args'])):
            if usedir:
                res = os.path.join(res, "")
            else:
                res += "_"
            res += "{" + self._name_pattern['args'][a] + "}"
        return res

    def set_active_arguments(self, **kwargs):
        """
        Overide all active arguments.
        """
        self._active_arguments = kwargs

    def update_active_arguments(self, store_value=True, **kwargs):
        """
        Update active arguments and extend arguments range.
        """
        for key, value in kwargs.iteritems():
            value_str = "{value}".format(value=value)
            self._active_arguments[key] = value_str
            if store_value:
                if self._arguments and key in self._arguments:
                    try:
                        self._arguments[key]["values"].index(value_str)
                    except ValueError:
                        self._arguments[key]["values"].append(value_str)
                else:
                    typechoice = "range"
                    if type(value) == type("String"):
                        typechoice = "list"
                    self.add_argument(key, [value], typechoice=typechoice)


    def set_name_pattern_string(self, string):
        """ call this when you already have a formatted string """
        components = re.split('{|}', str(string))
        if len(components) < 3: #[",'foo','_',...
            print string, "is an invalid name_pattern string"
            return
        separator = components[2]
        usedir = True
        if not separator in ['\\','/']:
           usedir = False
        args = []
        for a in range(1,len(components),2):
            args.append(components[a])
        self._name_pattern = {'usedir':usedir, 'args':args}

    def set_name_pattern(self, *args, **kwargs):
        """ call this when you just have a list of arguments """
        usedir = True
        if 'usedir' in kwargs:
            usedir = kwargs['usedir']
        self._name_pattern = {'usedir':usedir, 'args':args}

    def _expand_item(self, args):
        """
        given a partial list of arguments to specify an item, returns the fully
        qualified list with extraneous arguments removed and unspecified arguments
        replaced with defaults
        """
        #todo we probably want some general indexing too-
        #for a given arg set, what gidx does and 'places' does it correspond to and vice versa
        res = {}
        for x in self._arguments:
            if x in args:
                res[x] = args[x]
            else:
                res[x] = self._arguments[x]['default']
        return res

    def _find_directory(self, args):
        """
        returns directory where the requested item (specified as a set of arguments) lives
        """
        item = self._expand_item(args)
        base = self.get_directory()
        if not item or not base or not self._name_pattern:
            return None
        base = os.path.join(base, "")
        #note: pseudo-paramaters, like 'filename' and 'layer' are ignored
        #it is up to caller to deal with them
        for  x in self._name_pattern['args']:
            if x != 'filename':
                base += str(item[x])
                if self._name_pattern['usedir']:
                    base = os.path.join(base,"")
                else:
                    base += '_'
        base = base[0:-1] #strip trailing separator
        return base

    def _find_file(self, args):
        """path to a requested item (specified as a set of arguments)"""

        if args==None:
            args = self._active_arguments

        item = self._expand_item(args)
        directory = self._find_directory(item)

        if 'filename' in args:
            filename = args['filename']
##            if not filename in self._arguments['filename']['values']:
##                print ("warning looking for ", filename, " which is not in ",
##                    self._arguments['filename']['values'], " and thus unexpected")
        else:
            filename = self._arguments['filename']['default']

        if self._name_pattern['usedir']:
            fullname = os.path.join(directory, filename)
        else:
            fullname = directory + '_' + filename
        return fullname

    def load_item(self, handler, args=None):
        """
        call this to do something to something already in the data base
        requested item is specified by a set of arguments that distinguish it from others
        once found, we pass the filename for that, and the set of arguments, off to the
        provided handler function to take action on
        """
        if args==None:
            args = self._active_arguments
        item = self._expand_item(args) #redundant, but convenient
        fullname = self._find_file(args)
        result = handler(fullname, arguments=item)
        return result
 
    def save_item(self, payload, handler, args=None):
        """
        call this to add something to the data base
        args specifies what the item is for
        payload specifies what you are adding
        handler is a function that we call back to do to the actual writing
        """
        if args==None:
            args = self._active_arguments
        item = self._expand_item(args) #redundant, but convenient
        fullname = self._find_file(args)
        directory = os.path.dirname(fullname)
        if not os.path.exists(directory):
            os.makedirs(directory)
        result = None
        if handler:
            result = handler(fullname, payload, arguments=item)
        return result

    def next_set(self):
        """
        use this to walk through the store's set of items like so:

            def handler(fullname, payload, args)
                print args, fullname, payload
            for each, idx in cs.next_set():
                cs.save_item("foo", handle, each)

        this way the caller can easily drive an analysis on the store
        
        a generator to iterate though the ordered combination of arguments with.
        at each iteration it returns a map suitable for passing into load_item() or save_item()
        """
        ## todo, versions of this that return combinations of res, gidx, places so that you
        ## don't have to recieve but ignore them and uglify your calling code
        args = []
        values = []
        #valuesS = {}
        ordered = self._name_pattern['args']
        for name in ordered:
            a = self.get_argument(name)
            args.append(name)
            p = a['values']
            values.append(p)
            #valuesS[name] = p
        gidx = 0
        for element in itertools.product(*values):
            #places = []
            res = {}
            for idx in range(0,len(element)):
                    res[args[idx]] = element[idx]
                    #places.append(valuesS[args[idx]].index(element[idx]))
            yield res, gidx #, places
            gidx += 1
