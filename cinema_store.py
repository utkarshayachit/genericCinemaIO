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
import weakref

class Document(object):
    """Refers to a document in the Store."""
    def __init__(self, descriptor, data=None):
        self.__descriptor = descriptor
        self.__data = data
        self.__attributes = None

    @property
    def descriptor(self):
        """Returns the document descriptor. A document descriptor is a unique
        identifier for the document. It is a dict with key value pairs."""
        return self.__descriptor

    @property
    def attributes(self):
        """Returns the document attributes, if any. If no attributes are
        present, a None may be returned. Attributes are a dict with arbitrary
        meta-data relevant to the application."""
        return self.__attributes

    @attributes.setter
    def attributes(self, attrs):
        """Set document attributes"""
        self.__attributes = attrs

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, val):
        self.__data = val

class Store(object):
    """Base class for a cinema store. This class is an abstract class defining
    the API and storage independent logic. Storage specific subclasses handle
    the 'database' access."""

    def __init__(self):
        self.__metadata = None #better name is view hints
        self.__descriptor_definition = {}
        self.__loaded = False

    @property
    def descriptor_definition(self):
        return self.__descriptor_definition

    def _set_descriptor_definition(self, val):
        """For use by subclasses alone"""
        self.__descriptor_definition = val

    @property
    def metadata(self):
        return self.__metadata

    @metadata.setter
    def metadata(self, val):
        self.__metadata = val

    def add_metadata(self, keyval):
        if not self.__metadata:
            self.__metadata = {}
        self.__metadata.update(keyval)

    def get_full_descriptor(self, desc):
        # FIXME: bad name!!!
        full_desc = dict()
        for name, properties in self.descriptor_definition.items():
            if properties.has_key("default"):
                full_desc[name] = properties["default"]
        full_desc.update(desc)
        return full_desc

    def add_descriptor(self, name, properties):
        """Add a descriptor.

        :param name: Name for the descriptor.
        :param properties: Keyword arguments can be used to associate miscellaneous
        meta-data with this descriptor.
        """
        if self.__loaded:
            raise RuntimeError("Updating descriptors after loading/creating a store is not supported.")
        properties = self.validate_descriptor(name, properties)
        self.__descriptor_definition[name] = properties

    def get_descriptor_properties(self, name):
        return self.__descriptor_definition[name]

    def validate_descriptor(self, name, properties):
        """Validates a  new descriptor and return updated descriptor properties.
        Subclasses should override this as needed.
        """
        return properties

    def insert(self, document):
        """Inserts a new document"""
        if not self.__loaded:
            self.create()

    def load(self):
        assert not self.__loaded
        self.__loaded = True

    def create(self):
        assert not self.__loaded
        self.__loaded = True

    def find(self, q=None):
        raise RuntimeError("Subclasses must define this method")

class FileStore(Store):
    """Implementation of a store based on files and directories"""

    def __init__(self, dbfilename=None):
        super(FileStore, self).__init__()
        self.__filename_pattern = None
        self.__dbfilename = dbfilename if dbfilename \
                else os.path.join(os.getcwd(), "info.json")

    def load(self):
        """loads an existing filestore"""
        super(FileStore, self).load()
        with open(self.__dbfilename, mode="rb") as file:
            info_json = json.load(file)
            self._set_descriptor_definition(info_json['arguments'])
            self.metadata = info_json['metadata']
            self.__filename_pattern = info_json['name_pattern']

    def create(self):
        """creates a new file store"""
        super(FileStore, self).create()
        info_json = dict(
                arguments = self.descriptor_definition,
                name_pattern = self.filename_pattern,
                metadata = None
                )
        dirname = os.path.dirname(self.__dbfilename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(self.__dbfilename, mode="wb") as file:
            json.dump(info_json, file)

    @property
    def filename_pattern(self):
        return self.__filename_pattern

    @filename_pattern.setter
    def filename_pattern(self, val):
        self.__filename_pattern = val

    def insert(self, document):
        super(FileStore, self).insert(document)

        fname = self.get_filename(document)
        dirname = os.path.dirname(fname)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(fname, mode='w') as file:
            file.write(document.data)

        with open(fname + ".__data__", mode="w") as file:
            info_json = dict(
                    descriptor = document.descriptor,
                    attributes = document.attributes)
            json.dump(info_json, file)


    def get_filename(self, document):
        desc = self.get_full_descriptor(document.descriptor)
        suffix = self.filename_pattern.format(**desc)
        dirname = os.path.dirname(self.__dbfilename)
        return os.path.join(dirname, suffix)

    def find(self, q=None):
        q = q if q else dict()
        p = q
        for name, properties in self.descriptor_definition.items():
            if not name in q:
                p[name] = "*"

        dirname = os.path.dirname(self.__dbfilename)
        match_pattern = os.path.join(dirname, self.filename_pattern.format(**p))
        print match_pattern

        from fnmatch import fnmatch
        from os import walk
        for root, dirs, files in walk(os.path.dirname(self.__dbfilename)):
            for file in files:
                doc_file = os.path.join(root, file)
                if file.find("__data__") == -1 and fnmatch(doc_file, match_pattern):
                    yield self.load_document(doc_file)

    def load_document(self, doc_file):
        with open(doc_file + ".__data__", "r") as file:
            info_json = json.load(file)
        with open(doc_file, "r") as file:
            data = file.read()
        doc = Document(info_json["descriptor"], data)
        doc.attributes = info_json["attributes"]
        return doc


def make_cinema_descriptor_properties(name, values, **kwargs):
    default = kwargs['default'] if 'default' in kwargs else values[0]
    typechoice = kwargs['typechoice'] if 'typechoice' in kwargs else 'range'
    label = kwargs['label'] if 'label' in kwargs else name

    types = ['list','range']
    if not typechoice in types:
        raise RuntimeError, "Invalid typechoice, must be on of %s" % str(types)
    if not default in values:
        raise RuntimeError, "Invalid default, must be one of %s" % str(values)
    properties = dict()
    properties['type'] = typechoice
    properties['label'] = label
    properties['values'] = values
    properties['default'] = default
    return properties

#==============================================================================
# --------- OLD CODE ----------------------------------
#==============================================================================

class CinemaStore:
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

    def add_metadata(self, keyval):
        if not self._metadata:
            self._metadata = {}
        self._metadata.update(keyval)

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
