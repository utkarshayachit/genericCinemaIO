import cinemaDB
import itertools

class Explorer(object):
    """
    Middleman that connects an arbitrary producing code to the cinema_store.
    """

    def __init__(self,
        cinema_store,
        data_type,
        arguments, #these are the things that this explorer is responsible for and their ranges
        setup, # anything else we need to setup the engine
        engine, #the thing we pass off values to to do the work
        ):

        self.cinema_store = cinema_store
        self.arguments = arguments
        self.engine = engine
        if engine and setup:
            self.engine.prepare(setup)
        self.data_type = data_type

    def list_arguments(self):
        return [x for x in self.arguments.keys()]

    def get_data_type(self):
        return self.data_type

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
            args.append(name)
            vals = self.arguments[name]['values']
            if not name == 'filename':
                values.append(vals)
        gidx = 0
        for element in itertools.product(*values):
            res = {}
            for idx in range(0,len(element)):
                    res[args[idx]] = element[idx]
            self.execute(res)

class engine(object):
    """
    abstract interface for things that can produce data
    """

    def __init__(self):
        pass

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
