from PyQt5.QtCore import QObject

import numpy as np
from numpy.linalg import norm
from skimage.measure import marching_cubes
import os

from UM.Extension import Extension
from UM.Mesh.MeshData import MeshData
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.PluginRegistry import PluginRegistry

from cura.CuraApplication import CuraApplication
from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Scene.BuildPlateDecorator import BuildPlateDecorator
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator

def lerp(a, b, t):
    return (1-t)*a + b*t

def invlerp(val, a, b):
    return (val - a) / (b - a)

def map_range(val, min1, max1, min2, max2):
    return lerp(min2, max2, invlerp(val, min1, max1))

def compute_volume(span, resolution, f, g_min=0, g_max=1, offset=0.0):
    x, y, z = span * np.mgrid[g_min:g_max + resolution:resolution,
                              g_min:g_max + resolution:resolution,
                              g_min:g_max + resolution:resolution]
    return f(x,y,z, offset)

def gyroid(x,y,z, offset=0.0):
    def g(x,y,z):
        return np.sin(x)*np.cos(y) + np.sin(y)*np.cos(z) + np.sin(z)*np.cos(x)
    
    def dg(x,y,z):
        dx = np.cos(x)*np.cos(y) - np.sin(z)*np.sin(x)
        dy = -np.sin(x)*np.sin(y) + np.cos(y)*np.cos(z)
        dz = -np.sin(y)*np.sin(z) + np.cos(z)*np.cos(x)
        grad = np.stack((dx, dy, dz), axis=-1)
        grad = grad / np.linalg.norm(grad, axis=-1, keepdims=True)
        return grad
    
    if offset is 0.0:
        return g(x,y,z)

    # FIXME : Adding the z value to g does not correctly shift the level...
    grad = dg(x,y,z)
    return g(x,y,z) + grad[:,:,:,2]

def fks(x,y,z,level=0):
    def f(x,y,z):
        return np.cos(2*x)*np.sin(y)*np.cos(z) + np.cos(2*y)*np.sin(z)*np.cos(x) + np.cos(2*z)*np.sin(x)*np.cos(y)

    if level is 0.0:
        return f(x,y,z)
    return f(x,y,z)

class ImplicitModeller(Extension, QObject):
    def __init__(self, parent=None) -> None:
        QObject.__init__(self, parent)
        Extension.__init__(self)

        self._controller = CuraApplication.getInstance().getController()
        self._app = CuraApplication.getInstance()
        self._plugins = PluginRegistry.getInstance()
        self._dialog_window = None

        self.addMenuItem("Create Implicit Surface Dialog", self.openDialog)
    
    def openDialog(self) -> None:
        if not self._dialog_window:
            self._dialog_window = self._createDialog()
        self._dialog_window.accepted.connect(self.addImplicitSurface)
        self._dialog_window.open()
    
    def addImplicitSurface(self) -> None:
        implicitFunctionIndex = self._dialog_window.property('implicitFunctionIndex')
        if implicitFunctionIndex == 0:
            f = gyroid
            name = "Gyroid"
        elif implicitFunctionIndex == 1:
            f = fks
            name = "FisherKochS"

        periods = float(self._dialog_window.property('periods'))
        line_count = int(self._dialog_window.property('lineCount'))
        line_width = float(self._dialog_window.property('lineWidth'))
        dimensions = float(self._dialog_window.property('dimensions'))
        
        vertices, faces, normals = self._createImplicitSurface(f, periods, line_count, line_width, dimensions)
        self._addMeshToScene(name, vertices, faces, normals)
    
    def _createDialog(self) -> QObject:
        qml_file_path = os.path.join(
            self._plugins.getPluginPath(self.getPluginId()), "ImplicitModeller.qml"
        )
        modal = self._app.createQmlComponent(qml_file_path)

        return modal
    
    def _createImplicitSurface(self, f, periods, line_count, line_width, dimensions) -> None:
        volume = compute_volume(np.pi*2*periods, 0.01, f)
        vertices, faces, normals, _ = marching_cubes(volume, level=0)

        n = vertices.shape[0]
        vertices_flat = vertices.flatten()
        vertices = map_range(
            vertices_flat,
            0, np.max(vertices_flat),
            -dimensions * 0.5, dimensions * 0.5
        ).reshape((n,3))

        return vertices, faces, normals

    def _addMeshToScene(self, name, vertices, faces, normals):
        mesh_data = MeshData(vertices=vertices, normals=normals, indices=faces)

        node = CuraSceneNode()
        node.setMeshData(mesh_data)
        node.setSelectable(True)
        node.setName(f'{name}_{id(mesh_data)}')

        build_plate_id = self._app.getMultiBuildPlateModel().activeBuildPlate
        node.addDecorator(BuildPlateDecorator(build_plate_id))

        node.addDecorator(SliceableObjectDecorator())

        scene = self._controller.getScene()
        op = AddSceneNodeOperation(node , scene.getRoot())
        op.push()

        scene.sceneChanged.emit(node)