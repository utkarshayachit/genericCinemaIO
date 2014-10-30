import explorers

import paraview.simple as simple

class ImageExplorer(explorers.Explorer):

    def insert(self, document):
        # FIXME: for now we'll write a temporary image and read that in.
        # we need to provide nicer API for this.
        simple.WriteImage("temporary.png")
        with open("temporary.png", "rb") as file:
            document.data = file.read()
        super(ImageExplorer, self).insert(document)

class Camera(explorers.Engine):
    def __init__(self, center, axis, distance, view):
        super(Camera, self).__init__()
        try:
            # Z => 0 | Y => 2 | X => 1
            self.offset = (axis.index(1) + 1 ) % 3
        except ValueError:
            raise Exception("Rotation axis not supported", axis)
        self.center = center
        self.distance = distance
        self.view = view

    def execute(self, document):
        import math
        theta = document.descriptor['theta']
        phi = document.descriptor['phi']

        theta_rad = float(theta) / 180.0 * math.pi
        phi_rad = float(phi) / 180.0 * math.pi
        pos = [
            float(self.center[0]) - math.cos(phi_rad)   * self.distance * math.cos(theta_rad),
            float(self.center[1]) + math.sin(phi_rad)   * self.distance * math.cos(theta_rad),
            float(self.center[2]) + math.sin(theta_rad) * self.distance
            ]
        up = [
            + math.cos(phi_rad) * math.sin(theta_rad),
            - math.sin(phi_rad) * math.sin(theta_rad),
            + math.cos(theta_rad)
            ]
        self.view.CameraPosition = pos
        self.view.CameraViewUp = up
        self.view.CameraFocalPoint = self.center


class Slice(explorers.Engine):

    def __init__(self, argument, filt):
        super(Slice, self).__init__()

        self.argument = argument
        self.slice = filt

    def prepare(self, explorer):
        super(Slice, self).prepare(explorer)
        explorer.cinema_store.add_metadata({'type' : 'parametric-image-stack'})

    def execute(self, doc):
        o = doc.descriptor[self.argument]
        self.slice.SliceOffsetValues=[o]

class Contour(explorers.Engine):

    @classmethod
    def get_data_type(cls):
        return "parametric-image-stack"

    def __init__(self, argument, filt, iSave=False):
        explorers.Engine.__init__(self, iSave)

        self.argument = argument
        self.contour = filt
        self.control = 'Isosurfaces'

    def execute(self, arguments):
        o = arguments[self.argument]
        self.contour.SetPropertyWithName(self.control,[o])
        payload = None
        return payload

    def save(self, fullname, payload, arguments):
        if self.iSave:
            #print "SAVING", fullname, payload, arguments
            simple.WriteImage(fullname)

class Templated(explorers.Engine):

    @classmethod
    def get_data_type(cls):
        return "parametric-image-stack"

    def __init__(self, argument, filt, control, iSave=False):
        explorers.Engine.__init__(self, iSave)

        self.argument = argument
        self.filt = filt
        self.control = control

    def execute(self, arguments):
        o = arguments[self.argument]
        self.filt.SetPropertyWithName(self.control,[o])
        payload = None
        return payload

    def save(self, fullname, payload, arguments):
        if self.iSave:
            #print "SAVING", fullname, payload, arguments
            simple.WriteImage(fullname)

class ColorList():
    """
    A helper that creates a dictionary of color controls for ParaView. The Color engine takes in
    a Color name from the Explorer and looks up into a ColorList to determine exactly what
    needs to be set to apply the color.
    """
    def __init__(self):
        self._dict = {}

    def AddSolidColor(self, name, RGB):
        self._dict[name] = {'type':'rgb','content':RGB}

    def AddLUT(self, name, lut):
        self._dict[name] = {'type':'lut','content':lut}

    def getColor(self, name):
        return self._dict[name]

class Color(explorers.Engine):

    @classmethod
    def get_data_type(cls):
        return None

    def __init__(self, argument, colorlist, rep, iSave=True):
        explorers.Engine.__init__(self, iSave)
        self.argument = argument
        self.colorlist = colorlist
        self.rep = rep

    def execute(self, arguments):
        """ subclasses operate on arguments here and return a result """
        o = arguments[self.argument]
        spec = self.colorlist.getColor(o)
        if spec['type'] == 'rgb':
            self.rep.DiffuseColor = spec['content']
            self.rep.ColorArrayName = None
        if spec['type'] == 'lut':
            self.rep.LookupTable = spec['content']
            self.rep.ColorArrayName = o
        return None

    def save(self, fullname, payload, arguments):
        """ subclasses save off the payload here  """
        if self.iSave:
            #print "SAVING", fullname, payload, arguments
            simple.WriteImage(fullname)
