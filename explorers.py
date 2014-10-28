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

        self.cinema_store = cinema_store
        self.arguments = arguments
        self.engines = engines

        #any of the engines can declare that they define a particular cinema data
        #data type, which will inform the viewing apps what to do with the data
        if self.engines and self.cinema_store:
            for e in self.engines:
                dt = e.get_data_type()
                if dt:
                    self.cinema_store.add_metadata({'type':dt})

    def list_arguments(self):
        """
        arguments is an ordered list of parameters that the Explorer varies over
        """
        return self.arguments

    def prepare(self):
        """ Give engines a chance to get ready for a run """
        if self.engines:
            for e in self.engines:
                res = e.prepare()

    def execute(self, arguments):
        """ Execute 1 step. """
        self.cinema_store.update_active_arguments(arguments)

        if self.engines:
            for e in self.engines:
                res = e.execute(arguments)
                #engines may or may not do something in the save step
                #set up chains using iSave=True in the last engine's constructor
                self.cinema_store.save_item(res, e.save, args=arguments)

    def UpdatePipeline(self, arguments):
        """ Execute all steps. """

        self.prepare()

        #todo: should probably be a static method in cinema_store
        ordered = self.list_arguments()
        args = []
        values = []
        for name in ordered:
            vals = self.cinema_store.get_argument(name)['values']
            if not name == 'filename':
                args.append(name)
                values.append(vals)
        gidx = 0
        for element in itertools.product(*values):
            res = {}
            for idx in range(0,len(element)):
                    res[args[idx]] = element[idx]
            self.execute(res)

        self.finish()

    def finish(self):
        """ Give engines a chance to clean up after a run """
        if self.engines:
            for e in self.engines:
                res = e.finish()

class Engine(object):
    """
    abstract interface for things that can produce data

    to use this:
    caller should set up some visualization
    then tie a particular set of arguments to an action with an engine
    """

    def __init__(self, iSave=False):
        self.iSave = iSave

    @classmethod
    def get_data_type(cls):
        """
        subclasses return a cinema type string if they are want to write the cinema
        type into the info.json
        """
        return None

    def prepare(self):
        """ subclasses get ready to run here """
        pass

    def finish(self):
        """ subclasses cleanup after running here """
        pass

    def execute(self, arguments):
        """ subclasses operate on arguments here and return a result """
        payload = None
        return payload

    def save(self, fullname, payload, arguments):
        """ subclasses save off the payload here  """
        pass
