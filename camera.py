class CameraHandler(object):
    """
    Abstract interface to camera keyframes for cinema.
    maintains a 1:1 function, for indexes (into the set of parameter combinations) to camera states
    camera states consist of eye/posiiton, at/focal_point, and up vectors
    maintains an active index (which corresponds to a camera state)
    calling next() increments the active index
    calling update position makes the camera state take effect:
    *  updateing the supplied cinema_store to the parameters for the index and then
    *  passing off the corresponding camera state to a callback

    TODO: I am thinking that the bi-directional mapping and index should be more accessible
    """

    def __init__(self, cinema_store):
        self.cinema_store = cinema_store
        self.active_index = 0
        self.number_of_index = 0
        self.camera_positions = []
        self.camera_ups = []
        self.focal_point = [0,0,0]
        self.callback = None

    def set_callback(self, callback):
        self.callback = callback

    def reset(self):
        self.active_index = -1

    def __iter__(self):
        return self

    def next(self):
        if self.active_index + 1 < self.number_of_index:
            self.active_index += 1

            return self.active_index * 100 / self.number_of_index
        raise StopIteration()

    def apply_position(self):
        if self.callback:
            self.callback(self)

    def get_camera_keys(self):
        return []

    def get_camera_position(self):
        return self.camera_positions[self.active_index]

    def get_camera_view_up(self):
        return self.camera_ups[self.active_index]

    def get_camera_focal_point(self):
        return self.focal_point

# ==============================================================================

class ThreeSixtyCameraHandler(CameraHandler):
    """
    Camera for which the indices correspond to a set of positions on a sphere that is distance units away
    from a specified center.
    """
    def __init__(self, cinema_store, phis, thetas, center, axis, distance):
        import math

        CameraHandler.__init__(self, cinema_store)
        self.phi = []
        self.theta = []
        self.active_index = 0
        self.focal_point = center

        try:
            # Z => 0 | Y => 2 | X => 1
            self.offset = (axis.index(1) + 1 ) % 3
        except ValueError:
            raise Exception("Rotation axis not supported", axis)

        for theta in thetas:
            theta_rad = float(theta) / 180.0 * math.pi
            for phi in phis:
                phi_rad = float(phi) / 180.0 * math.pi

                pos = [
                    float(center[0]) - math.cos(phi_rad)   * distance * math.cos(theta_rad),
                    float(center[1]) + math.sin(phi_rad)   * distance * math.cos(theta_rad),
                    float(center[2]) + math.sin(theta_rad) * distance
                    ]
                up = [
                    + math.cos(phi_rad) * math.sin(theta_rad),
                    - math.sin(phi_rad) * math.sin(theta_rad),
                    + math.cos(theta_rad)
                    ]

                # Handle rotation around Z => 0 | Y => 2 | X => 1
                for i in range(self.offset):
                    pos.insert(0, pos.pop())
                    up.insert(0, up.pop())

                # Save information
                self.camera_positions.append(pos)
                self.camera_ups.append(up)
                self.phi.append(phi)
                self.theta.append(theta + 90)

        self.number_of_index = len(self.phi)

    def get_camera_keys(self):
        return ['phi', 'theta']

    def apply_position(self):
        self.cinema_store.update_active_arguments(phi=self.phi[self.active_index])
        self.cinema_store.update_active_arguments(theta=self.theta[self.active_index])
        super(ThreeSixtyCameraHandler, self).apply_position()
