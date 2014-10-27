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

class Color(explorers.Engine):
    def __init__(self, argument, rep):
        super(Color, self).__init__()
        self.argument = argument
        self.rep = rep

    def execute(self, doc):
        o = doc.descriptor[self.argument]
        self.rep.DiffuseColor = o
