import cinema_store
import itertools

class Explorer(object):
    """
    Middleman that connects an arbitrary producing codes to the CinemaStore.
    The purpose of this class is to run through the argument sets, and tell a
    set of engines (in order) to do something with the arguments it cares about.
    """

    def __init__(self,
        cinema_store,
        arguments, #these are the things that this explorer is responsible for and their ranges
        engines #the thing we pass off values to to do the work
        ):

        self.__cinema_store = cinema_store
        self.arguments = arguments
        self.engines = engines

    @property
    def cinema_store(self):
        return self.__cinema_store

    def list_arguments(self):
        """
        arguments is an ordered list of parameters that the Explorer varies over
        """
        return self.arguments

    def prepare(self):
        """ Give engines a chance to get ready for a run """
        if self.engines:
            for e in self.engines:
                res = e.prepare(self)

    def execute(self, desc):
        # Create the document/data product for this sample.
        doc = cinema_store.Document(desc)
        for e in self.engines:
            e.execute(doc)
        self.insert(doc)

    def explore(self):
        """Explore the problem space to populate the store"""
        self.prepare()

        ordered = self.list_arguments()
        args = []
        values = []
        for name in ordered:
            vals = self.cinema_store.get_descriptor_properties(name)['values']
            args.append(name)
            values.append(vals)

        for element in itertools.product(*values):
            desc = dict(itertools.izip(args, element))
            self.execute(desc)

        self.finish()

    def finish(self):
        """ Give engines a chance to clean up after a run """
        if self.engines:
            for e in self.engines:
                res = e.finish()

    def insert(self, doc):
        self.cinema_store.insert(doc)

class Engine(object):
    """
    abstract interface for things that can produce data

    to use this:
    caller should set up some visualization
    then tie a particular set of arguments to an action with an engine
    """

    def __init__(self):
        pass

    def prepare(self, explorer):
        """ subclasses get ready to run here """
        pass

    def finish(self):
        """ subclasses cleanup after running here """
        pass

    def execute(self, document):
        """ subclasses operate on arguments here"""
        pass
