import explorers

import paraview.simple as simple

class Slice(explorers.Engine):

    #    import sys
    #    sys.path.append("/Builds/ParaView/devel/master_debug/lib")
    #    sys.path.append("/Builds/ParaView/devel/master_debug/lib/site-packages")

    @classmethod
    def get_data_type(cls):
        return "parametric-image-stack"

    def __init__(self):
        explorers.Engine.__init__(self)

    def prepare(self, setup):
        """ subclasses take whatever is in setup here and use it to get ready """

        data = setup

        self.view_proxy = simple.CreateRenderView()
        self.slice = simple.Slice( SliceType="Plane", Input=data, SliceOffsetValues=[0.0] )
        self.sliceRepresentation = simple.Show(self.slice)
        #self.colorByArray = colorByArray
        #self.parallelScaleRatio = parallelScaleRatio
        #self.slice.SliceType.Normal = normal
        self.dataBounds = data.GetDataInformation().GetBounds()
        #self.normal = normal
        #self.viewup = viewup
        #self.origin = [ self.dataBounds[0] + bound_range[0] * (self.dataBounds[1] - self.dataBounds[0]),
        #                self.dataBounds[2] + bound_range[0] * (self.dataBounds[3] - self.dataBounds[2]),
        #                self.dataBounds[4] + bound_range[0] * (self.dataBounds[5] - self.dataBounds[4]) ]
        #self.number_of_steps = steps
        #ratio = (bound_range[1] - bound_range[0]) / float(steps-1)
        #self.origin_inc = [ normal[0] * ratio * (self.dataBounds[1] - self.dataBounds[0]),
        #                    normal[1] * ratio * (self.dataBounds[3] - self.dataBounds[2]),
        #                    normal[2] * ratio * (self.dataBounds[5] - self.dataBounds[4]) ]


    def execute(self, arguments):
        """ subclasses operate on arguments here and return a result """
        o = arguments['offset']
        self.slice.SliceOffsetValues=[o]
        simple.Render()
        payload = None
        return payload

    def save(self, fullname, payload, arguments):
        """ subclasses save off the payload here  """
        print "SAVING", fullname, payload, arguments
        simple.WriteImage(fullname)
