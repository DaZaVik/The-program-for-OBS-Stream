from pygrabber.dshow_graph import FilterGraph

class cam_check:

    def get_camera_names(self):
        graph = FilterGraph()
        self.cameras = graph.get_input_devices()
        return self.cameras
