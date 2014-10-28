import explorers

import paraview.simple as simple

class Camera(explorers.Engine):

    @classmethod
    def get_data_type(cls):
        return None

    def __init__(self, center, axis, distance, view, iSave=False):

        explorers.Engine.__init__(self, iSave)
        try:
            # Z => 0 | Y => 2 | X => 1
            self.offset = (axis.index(1) + 1 ) % 3
        except ValueError:
            raise Exception("Rotation axis not supported", axis)
        self.center = center
        self.distance = distance
        self.view = view

    def execute(self, arguments):
        import math

        theta = arguments['theta']
        phi = arguments['phi']

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

        return None

    def save(self, fullname, payload, arguments):
        if self.iSave:
            #print "SAVING", fullname, payload, arguments
            simple.WriteImage(fullname)


class Slice(explorers.Engine):

    @classmethod
    def get_data_type(cls):
        return "parametric-image-stack"

    def __init__(self, argument, filt, iSave=False):
        explorers.Engine.__init__(self, iSave)

        self.argument = argument
        self.slice = filt

    def execute(self, arguments):
        """ subclasses operate on arguments here and return a result """
        o = arguments[self.argument]
        self.slice.SliceOffsetValues=[o]
        payload = None
        return payload

    def save(self, fullname, payload, arguments):
        """ subclasses save off the payload here  """
        if self.iSave:
            #print "SAVING", fullname, payload, arguments
            simple.WriteImage(fullname)

class Color(explorers.Engine):
    @classmethod
    def get_data_type(cls):
        return None

    def __init__(self, argument, rep, iSave=True):
        explorers.Engine.__init__(self, iSave)
        self.argument = argument
        self.rep = rep

    def execute(self, arguments):
        """ subclasses operate on arguments here and return a result """
        o = arguments[self.argument]
        self.rep.DiffuseColor = o
        payload = None
        return payload

    def save(self, fullname, payload, arguments):
        """ subclasses save off the payload here  """
        if self.iSave:
            #print "SAVING", fullname, payload, arguments
            simple.WriteImage(fullname)
