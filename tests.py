"""
This module tests the generic interface to cinema data.
"""

from cinema_store import *

def test_read(fname = None, silent = True):
    if not fname:
        fname = "info.json"
    cs = CinemaStore(fname)
    if not cs.verify():
        print "problem with that file"
        return None

    if not silent:
        print "CS", cs
        print "ARGS", cs.get_arguments()
        print "NPS", cs.get_name_pattern_string()
        print "MD", cs.get_metadata()
    return cs

def test_argument(fname = None):
    cs = test_read(fname, True)

    if not cs:
        return

    print "* before"
    args = cs.get_arguments()
    for x in args:
        print x, "\t", args[x]

    a = cs.add_argument("theta", [0,45,90,135,180])

    print "* after"
    args = cs.get_arguments()
    for x in args:
        print x, "\t", args[x]

def test_name_pattern():
    cs = CinemaStore("info.json")
    cs.set_name_pattern("time","theta","range")
    print(cs.get_name_pattern_string())
    cs.set_name_pattern("theta","time","range",usedir=True)
    print(cs.get_name_pattern_string())
    cs.set_name_pattern("theta","time","range",usedir=False)
    print(cs.get_name_pattern_string())

def test_write(fname=None):
    if not fname:
        fname = "info.json"
    cs = CinemaStore(fname)

    cs.set_metadata = {"testing":123}
    a = cs.add_argument("theta", [0,45,90,135,180])
    a = cs.add_argument("filename", ["rgb.png"], typechoice='list')
    cs.misc_json["miscelaneous"] = "vilanous"
    cs.set_name_pattern_string("{theta}")
    cs.write_json(fname)
    return cs

def test_load_item(fname = None):
    def handler(fullname,arguments):
        import hashlib
        import os
        if not os.path.exists(fullname):
            print fullname, "is missing"
        else:
            print fullname, hashlib.md5(open(fullname, 'rb').read()).hexdigest()
    cs = test_read(fname)
    res = cs.load_item(handler, {'phi':120,'time':10,'filename':'nada.txt'})
    res = cs.load_item(handler, {'phi':120,'time':10,'filename':'rgb.png'})

def test_save_item(fname = None):
    def handler(fullname, item, arguments):
        fd = open(fullname, 'w')
        fd.write(item)
        fd.close()
    cs = test_read(fname)
    res = cs.save_item( "The quick brown fox jumped over the lazy dog.\n", handler, {'phi':120,'time':10,'filename':'event.txt'})

def test_next(fname=None):
    def handler(fullname, arguments):
        print fullname, arguments

    cs = test_read(fname)
    cs.add_argument("phi", [0,45,90,135,180])
    cs.set_name_pattern("theta","phi")

    for args, idx in cs.next_set():
        cs.load_item(handler, args)

def demonstrate_populate(fname="info.json"):
    """ this demonstrates populating a new cinema store from a flat list of files."""
    cs = CinemaStore(fname)
    cs.set_name_pattern_string("{theta}/{phi}")
    cs.add_argument("theta", [0,10,20,30,40])
    cs.add_argument("phi", [0,10,20,30,40])
    cs.write_json()

    def handler(fullname, ifile, arguments):
        import shutil
        print "cp", ifile, fullname
        shutil.copyfile(ifile, fullname)

    for args, idx in cs.next_set():
        ifile = "/Users/demarle/tmp/infiles/file_" + str(idx) + ".txt"
        args['filename']="copy2"
        cs.save_item(ifile, handler, args)

def demonstrate_analyze(fname="info.json"):
    """
    this demonstrates traversing an existing cinema store and doing some analysis
    (in this case just printing the contents) on each item
    """
    cs = CinemaStore(fname)

    def handler(fullname, arguments):
        print fullname
        fd = open(fullname, 'r')
        for line in fd:
            print line
        fd.close()

    for args, idx in cs.next_set():
        args['filename']="copy2"
        cs.load_item(handler, args)


def test_camera(fname="info.json"):
    """
    tests the 360 camera handler by making one and setting up a vtk pipeline
    that it controls and dumps images out into the data base from.
    """
    import camera
    cs = CinemaStore(fname)
    cs.set_name_pattern_string("{phi}/{theta}")
    cs.add_argument('filename','rgb.png')
    cam = camera.ThreeSixtyCameraHandler(
        cs,
        [180], [-180,-150,-120,-90,-60,-30,0,30,60,90,120,150,180], [0,0,0],
        [1,0,0], 5)
    sys.path.append("/Builds/VTK/devel/master/lib")
    sys.path.append("/Builds/VTK/devel/master/lib/site-packages/")
    sys.path.append("/Builds/VTK/devel/master/Wrapping/Python/")

    import vtk
    rw = vtk.vtkRenderWindow()
    r = vtk.vtkRenderer()
    rw.AddRenderer(r)
    s = vtk.vtkSphereSource()
    m = vtk.vtkPolyDataMapper()
    m.SetInputConnection(s.GetOutputPort())
    a = vtk.vtkActor()
    a.SetMapper(m)
    r.AddActor(a)
    rw.Render()
    c = r.GetActiveCamera()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(rw)
    pw = vtk.vtkPNGWriter()
    pw.SetInputConnection(w2i.GetOutputPort())

    def handler(cam):
        p = cam.get_camera_position()
        c.SetPosition(p[0],p[1],p[2])
        u = cam.get_camera_view_up()
        c.SetViewUp(u[0],u[1],u[2])
        f = cam.get_camera_focal_point()
        c.SetFocalPoint(f[0],f[1],f[2])
        r.ResetCameraClippingRange()
        rw.Render()
        w2i.Modified()

        cs.save_item("",None)
        pt = cs._active_arguments
        pt['filename'] = 'rgb.png'
        fn = cs._find_file(pt)
        pw.SetFileName(fn);
        pw.Write()

    cam.set_callback(handler)

    for x in cam:
        cam.apply_position()

    cs.write_json()
    return cam

def test_Explorer():
    import explorers

    cs = CinemaStore('info.json')
    cs.get_arguments()
    e = explorers.Explorer(cs, cs.get_arguments(), None, None)
    print "ARGS", e.list_arguments()
    print "DT", e.get_data_type()
    e.UpdatePipeline("NONE")

    print "*"*40
    g = explorers.Engine()
    e = explorers.Explorer(cs, cs.get_arguments(), "hey man", g)
    e.UpdatePipeline("NONE")

    return e

def test_vtk_slice(fname):
    import explorers
    import vtk_explorers
    import vtk

    s = vtk.vtkSphereSource()

    if not fname:
        fname = "info.json"
    cs = CinemaStore(fname)
    cs.set_name_pattern_string("{offset}_{filename}")
    a = cs.add_argument("offset", [0,.2,.4,.6,.8,1.0])
    a = cs.add_argument("filename", ['slice.png'])

    g = vtk_explorers.Slice()
    e = explorers.Explorer(cs, cs.get_arguments(), s, g)
    e.UpdatePipeline("NONE")

    cs.write_json()

    return e

def test_pv_slice(fname):
    import explorers
    import pv_explorers
    import paraview.simple

    s = paraview.simple.Sphere()

    if not fname:
        fname = "info.json"
    cs = CinemaStore(fname)
    cs.set_name_pattern_string("{offset}_{filename}")
    a = cs.add_argument("offset", [0,.2,.4,.6,.8,1.0])
    a = cs.add_argument("filename", ['slice.png'])

    g = pv_explorers.Slice()
    e = explorers.Explorer(cs, cs.get_arguments(), s, g)
    e.UpdatePipeline("NONE")

    cs.write_json()

    return e


if __name__ == "__main__":
    None
