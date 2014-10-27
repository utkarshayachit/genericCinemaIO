import cinema_store
import itertools

class Explorer(object):
    """
    Middleman that connects an arbitrary producing code to the CinemaStore.
    """

    def __init__(self,
        cinema_store,
        arguments, #these are the things that this explorer is responsible for and their ranges
        setup, # anything else we need to setup the engine
        engine, #the thing we pass off values to to do the work
        ):

        self.cinema_store = cinema_store
        self.arguments = arguments
        self.engine = engine
        if engine and setup:
            self.engine.prepare(setup)
            self.cinema_store.add_metadata({'type':engine.get_data_type()})

    def list_arguments(self):
        return self.arguments.keys()

    def execute(self, arguments):
        """ Excecute 1 step. """
        self.cinema_store.update_active_arguments(arguments)

        if self.engine:
            res = self.engine.execute(arguments)
            self.cinema_store.save_item(res, self.engine.save, args=arguments)

    def UpdatePipeline(self, arguments):
        """ Execute all steps. """

        #todo: move this into a static method in cinema_store
        ordered = self.list_arguments()
        args = []
        values = []
        for name in ordered:
            vals = self.arguments[name]['values']
            if not name == 'filename':
                args.append(name)
                values.append(vals)
        gidx = 0
        for element in itertools.product(*values):
            res = {}
            for idx in range(0,len(element)):
                    res[args[idx]] = element[idx]
            self.execute(res)

class Engine(object):
    """
    abstract interface for things that can produce data
    """

    def __init__(self):
        pass

    @classmethod
    def get_data_type(cls):
        return "experimental"

    def prepare(self, setup):
        """ subclasses take whatever is in setup here and use it to get ready """
        print "SETUP", setup

    def execute(self, arguments):
        """ subclasses operate on arguments here and return a result """
        print "EXECUTE", arguments
        payload = None
        return payload

    def save(self, fullname, payload, arguments):
        """ subclasses save off the payload here  """
        print "SAVING", fullname, payload, arguments
