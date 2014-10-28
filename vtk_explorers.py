import explorers
import vtk

class Clip(explorers.Engine):

    @classmethod
    def get_data_type(cls):
        return "parametric-image-stack"

    def __init__(self, argument, clip, rw, iSave=True):
        explorers.Engine.__init__(self, iSave)
        self.argument = argument

        self.clip = clip
        self.rw = rw

        self.w2i = vtk.vtkWindowToImageFilter()
        self.w2i.SetInput(self.rw)

        self.pw = vtk.vtkPNGWriter()
        self.pw.SetInputConnection(self.w2i.GetOutputPort())

    def execute(self, arguments):
        """ subclasses operate on arguments here and return a result """
        o = arguments[self.argument]
        self.clip.SetValue(o)

        payload = None
        return payload

    def save(self, fullname, payload, arguments):
        """ subclasses save off the payload here  """
        if iSave:
            #print "SAVING", fullname, payload, arguments
            self.rw.Render()
            self.w2i.Modified()
            self.pw.SetFileName(fullname)
            self.pw.Write()
