import explorers
import vtk

class slice_engine(explorers.engine):

    def __init__(self):
        explorers.engine.__init__(self)

        rw = vtk.vtkRenderWindow()
        self.rw = rw

        r = vtk.vtkRenderer()
        rw.AddRenderer(r)
        s = vtk.vtkSphereSource()

        normals = vtk.vtkPolyDataNormals()
        normals.SetInputConnection(s.GetOutputPort())

        plane = vtk.vtkPlane()
        plane.SetOrigin(0, 0, 0)
        plane.SetNormal(-1, -1, 0)

        clipper = vtk.vtkClipPolyData()
        clipper.SetInputConnection(normals.GetOutputPort())
        clipper.SetClipFunction(plane)
        clipper.GenerateClipScalarsOn()
        clipper.GenerateClippedOutputOn()
        clipper.SetValue(0.5)
        self.clipper = clipper

        m = vtk.vtkPolyDataMapper()
        m.SetInputConnection(clipper.GetOutputPort())

        a = vtk.vtkActor()
        a.SetMapper(m)
        r.AddActor(a)
        rw.Render()

        w2i = vtk.vtkWindowToImageFilter()
        w2i.SetInput(rw)
        self.w2i = w2i

        pw = vtk.vtkPNGWriter()
        pw.SetInputConnection(w2i.GetOutputPort())
        self.pw = pw

    def prepare(self, setup):
        """ subclasses take whatever is in setup here and use it to get ready """
        print "SETUP", setup

    def execute(self, arguments):
        """ subclasses operate on arguments here and return a result """
        o = arguments['offset']
        print "EXECUTE", arguments, o
        self.clipper.SetValue(o)
        self.rw.Render()
        self.w2i.Modified()
        payload = None
        return payload

    def save(self, fullname, payload, arguments):
        """ subclasses save off the payload here  """
        print "SAVING", fullname, payload, arguments
        self.pw.SetFileName(fullname)
        self.pw.Write()
