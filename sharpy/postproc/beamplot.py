import sharpy.utils.cout_utils as cout
from sharpy.presharpy.utils.settings import str2bool
from sharpy.utils.solver_interface import solver, BaseSolver

from tvtk.api import tvtk, write_data
import numpy as np
import os


@solver
class BeamPlot(BaseSolver):
    solver_id = 'BeamPlot'
    solver_type = 'postproc'
    solver_unsteady = False

    def __init__(self):
        self.ts = 0  # steady solver
        pass

    def initialise(self, data):
        self.data = data
        self.settings = data.settings[self.solver_id]
        self.convert_settings()

    def run(self):
        # create folder for containing files if necessary
        if not os.path.exists(self.settings['route']):
            os.makedirs(self.settings['route'])
        self.plot()
        cout.cout_wrap('...Finished', 1)
        return self.data

    def convert_settings(self):
        try:
            self.settings['route'] = (str2bool(self.settings['route']))
        except KeyError:
            cout.cout_wrap(self.solver_id + ': no location for figures defined, defaulting to ./output', 3)
            self.settings['route'] = './output'
        pass

    def plot(self):
        filename = '%s_beam' % (self.data.settings['SHARPy']['case'])
        num_nodes = self.data.beam.num_node
        num_elem = self.data.beam.num_elem

        coords = np.zeros((num_nodes, 3))
        conn = np.zeros((num_elem, 3), dtype=int)
        node_id = np.zeros((num_nodes,), dtype=int)
        elem_id = np.zeros((num_elem,), dtype=int)
        local_x = np.zeros((num_nodes, 3))
        local_y = np.zeros((num_nodes, 3))
        local_z = np.zeros((num_nodes, 3))
        # coordinates of corners
        for i_node in range(num_nodes):
            coords[i_node, :] = self.data.beam.pos_def[i_node, :]

        for i_node in range(num_nodes):
            i_elem = self.data.beam.node_master_elem[i_node, 0]
            i_local_node = self.data.beam.node_master_elem[i_node, 1]
            node_id[i_node] = i_node

            v1, v2, v3 = self.data.beam.elements[i_elem].deformed_triad()
            local_x[i_node, :] = v1[i_local_node, :]
            local_y[i_node, :] = v2[i_local_node, :]
            local_z[i_node, :] = v3[i_local_node, :]

        for i_elem in range(num_elem):
            conn[i_elem, :] = self.data.beam.elements[i_elem].reordered_global_connectivities
            elem_id[i_elem] = i_elem

        ug = tvtk.UnstructuredGrid(points=coords)
        ug.set_cells(tvtk.Line().cell_type, conn)
        ug.cell_data.scalars = elem_id
        ug.cell_data.scalars.name = 'elem_id'
        ug.point_data.scalars = node_id
        ug.point_data.scalars.name = 'node_id'
        ug.point_data.add_array(local_x, 'vector')
        ug.point_data.get_array(1).name = 'local_x'
        ug.point_data.add_array(local_y, 'vector')
        ug.point_data.get_array(2).name = 'local_y'
        ug.point_data.add_array(local_z, 'vector')
        ug.point_data.get_array(3).name = 'local_z'
        write_data(ug, filename)

