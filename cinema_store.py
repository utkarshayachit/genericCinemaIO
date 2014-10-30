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
