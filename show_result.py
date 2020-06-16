from PySide2.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider
from PySide2.QtGui import QShowEvent, QCloseEvent, Qt
from vtk.qt4.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk import vtkImagePlaneWidget, vtkImageData, vtkRenderer, vtkInteractorStyleTrackballCamera, vtkDiscreteMarchingCubes, vtkImageImport, vtkLookupTable, vtkPolyDataMapper, vtkActor
from numpy import flip, array
# import time


class ShowResultWindow(QDialog):

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        ###��ά��ʾ����###
        self.vtkwidget_3d = QVTKRenderWindowInteractor(self)
        self.vtkwidget_3d.GlobalWarningDisplayOff()
        self.vtkwidget_3d.setMinimumSize(512, 512)
        self.renderwindow_3d = self.vtkwidget_3d.GetRenderWindow()
        self.iren_3d = self.renderwindow_3d.GetInteractor()
        self.ren_3d = vtkRenderer()
        self.renderwindow_3d.AddRenderer(self.ren_3d)
        ###��ά��ʾ����###
        # self.vtkwidget_2d = QVTKRenderWindowInteractor(self)
        # self.vtkwidget_2d.GlobalWarningDisplayOff()
        # self.vtkwidget_2d.setMinimumSize(512, 512)
        # self.renderwindow_2d = self.vtkwidget_2d.GetRenderWindow()
        # self.iren_2d = self.renderwindow_2d.GetInteractor()
        # self.ren_2d = vtkRenderer()
        # self.renderwindow_2d.AddRenderer(self.ren_2d)
        ###����###
        self.sliber = QSlider()
        self.sliber.setOrientation(Qt.Horizontal)
        self.sliber.valueChanged.connect(self.sliber_value_changed)
        ###slice������ǩ###
        self.slice_num_label = QLabel(self)
        self.slice_num_label.setAlignment(Qt.AlignCenter)
        label_font = self.slice_num_label.font()
        label_font.setPointSize(16)
        self.slice_num_label.setFont(label_font)
        ###��ʾ�ؼ�����###
        self.show_result_layout = QHBoxLayout()
        self.show_result_layout.addWidget(self.vtkwidget_3d)
        # self.show_result_layout.addWidget(self.vtkwidget_2d)
        ###������###
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.slice_num_label)
        self.main_layout.addWidget(self.sliber)
        self.main_layout.addLayout(self.show_result_layout)
        self.setLayout(self.main_layout)

        ###���ݳ�ʼ��###
        self.wholeExtent = []
        self.point_list = []
        self.point_z = []
        self.Image = vtkImageData()
        self.TextureInterpolation = 1
        self.dicom_images_3d = vtkImageImport()
        self.dicom_images_2d = vtkImageImport()
        self.label = array(self.wholeExtent)
        self.label_2d = array(self.wholeExtent)
        self.spacing = []

        ###�����ʼ��###
        self.iren_3d.SetInteractorStyle(vtkInteractorStyleTrackballCamera())
        self.iren_3d.GetInteractorStyle().KeyPressActivationOff()
        self.iren_3d.GetInteractorStyle().AddObserver("MouseWheelBackwardEvent", self.last_slice)
        self.iren_3d.GetInteractorStyle().AddObserver("MouseWheelForwardEvent", self.next_slice)
        self.PlaneWidgetY_3d = vtkImagePlaneWidget()
        self.PlaneWidgetY_3d.SetInteractor(self.iren_3d)
        self.PlaneWidgetZ_3d = vtkImagePlaneWidget()
        self.PlaneWidgetZ_3d.SetInteractor(self.iren_3d)
        self.PlaneWidgetY_3d.SetResliceInterpolateToLinear()
        self.PlaneWidgetY_3d.SetTextureInterpolate(self.TextureInterpolation)
        self.PlaneWidgetY_3d.SetPlaneOrientationToYAxes()
        self.PlaneWidgetY_3d.DisplayTextOff()
        self.PlaneWidgetY_3d.KeyPressActivationOff()
        self.PlaneWidgetY_3d.InteractionOff()
        self.PlaneWidgetZ_3d.SetResliceInterpolateToLinear()
        self.PlaneWidgetZ_3d.SetTextureInterpolate(self.TextureInterpolation)
        self.PlaneWidgetZ_3d.SetPlaneOrientationToZAxes()
        self.PlaneWidgetZ_3d.DisplayTextOn()
        self.PlaneWidgetZ_3d.KeyPressActivationOff()
        self.PlaneWidgetZ_3d.SetLeftButtonAction(self.PlaneWidgetZ_3d.VTK_WINDOW_LEVEL_ACTION)
        self.PlaneWidgetZ_3d.SetRightButtonAction(self.PlaneWidgetZ_3d.VTK_CURSOR_ACTION)
        self.PlaneWidgetZ_3d.SetMiddleButtonAction(self.PlaneWidgetZ_3d.VTK_CURSOR_ACTION)

        # self.iren_2d.SetInteractorStyle(vtkInteractorStyleTrackballCamera())
        # self.iren_2d.GetInteractorStyle().KeyPressActivationOff()
        # self.iren_2d.GetInteractorStyle().AddObserver("MouseWheelBackwardEvent", self.last_slice)
        # self.iren_2d.GetInteractorStyle().AddObserver("MouseWheelForwardEvent", self.next_slice)
        # self.PlaneWidgetY_2d = vtkImagePlaneWidget()
        # self.PlaneWidgetY_2d.SetInteractor(self.iren_2d)
        # self.PlaneWidgetZ_2d = vtkImagePlaneWidget()
        # self.PlaneWidgetZ_2d.SetInteractor(self.iren_2d)
        # self.PlaneWidgetY_2d.SetResliceInterpolateToLinear()
        # self.PlaneWidgetY_2d.SetTextureInterpolate(self.TextureInterpolation)
        # self.PlaneWidgetY_2d.SetPlaneOrientationToYAxes()
        # self.PlaneWidgetY_2d.DisplayTextOff()
        # self.PlaneWidgetY_2d.KeyPressActivationOff()
        # self.PlaneWidgetY_2d.InteractionOff()
        # self.PlaneWidgetZ_2d.SetResliceInterpolateToLinear()
        # self.PlaneWidgetZ_2d.SetTextureInterpolate(self.TextureInterpolation)
        # self.PlaneWidgetZ_2d.SetPlaneOrientationToZAxes()
        # self.PlaneWidgetZ_2d.DisplayTextOn()
        # self.PlaneWidgetZ_2d.KeyPressActivationOff()
        # self.PlaneWidgetZ_2d.SetLeftButtonAction(self.PlaneWidgetZ_2d.VTK_WINDOW_LEVEL_ACTION)
        # self.PlaneWidgetZ_2d.SetRightButtonAction(self.PlaneWidgetZ_2d.VTK_CURSOR_ACTION)
        # self.PlaneWidgetZ_2d.SetMiddleButtonAction(self.PlaneWidgetZ_2d.VTK_CURSOR_ACTION)

    def sliber_value_changed(self):
        # self.label_2d = np.zeros_like(self.label)
        # self.label_2d[self.sliber.value(), :, :] = self.label[self.sliber.value(), :, :]
        # self.dicom_images_2d.CopyImportVoidPointer(self.label_2d.tostring(), len(self.label_2d.tostring()))
        # self.dicom_images_2d.Update()
        # self.discrete_marching_cubes_2d.Update()
        # self.dicom_data_mapper_2d.Update()
        self.PlaneWidgetZ_3d.SetSliceIndex(self.sliber.value())
        # self.PlaneWidgetZ_2d.SetSliceIndex(self.sliber.value())
        self.slice_num_label.setText(str(self.PlaneWidgetZ_3d.GetSliceIndex()))
        self.renderwindow_3d.Render()
        # self.renderwindow_2d.Render()

    def last_slice(self, obj, ev):
        slice_number = self.PlaneWidgetZ_3d.GetSliceIndex()
        # self.label_2d = np.zeros_like(self.label)
        # self.label_2d[slice_number, :, :] = self.label[slice_number, :, :]
        # self.dicom_images_2d.CopyImportVoidPointer(self.label_2d.tostring(), len(self.label_2d.tostring()))
        # self.dicom_images_2d.Update()
        # self.discrete_marching_cubes_2d.Update()
        # self.dicom_data_mapper_2d.Update()
        self.PlaneWidgetZ_3d.SetSliceIndex((slice_number - 1) % self.wholeExtent[5])
        # self.PlaneWidgetZ_2d.SetSliceIndex((slice_number - 1) % self.wholeExtent[5])
        self.slice_num_label.setText(str(self.PlaneWidgetZ_3d.GetSliceIndex()))
        self.sliber.setValue(slice_number - 1)
        self.renderwindow_3d.Render()
        # self.renderwindow_2d.Render()

    def next_slice(self, obj, ev):
        slice_number = self.PlaneWidgetZ_3d.GetSliceIndex()
        # self.label_2d = np.zeros_like(self.label)
        # self.label_2d[slice_number, :, :] = self.label[slice_number, :, :]
        # self.dicom_images_2d.CopyImportVoidPointer(self.label_2d.tostring(), len(self.label_2d.tostring()))
        # self.dicom_images_2d.Update()
        # self.discrete_marching_cubes_2d.Update()
        # self.dicom_data_mapper_2d.Update()
        self.PlaneWidgetZ_3d.SetSliceIndex((slice_number + 1) % self.wholeExtent[5])
        # self.PlaneWidgetZ_2d.SetSliceIndex((slice_number + 1) % self.wholeExtent[5])
        self.slice_num_label.setText(str(self.PlaneWidgetZ_3d.GetSliceIndex()))
        self.sliber.setValue(slice_number + 1)
        self.renderwindow_3d.Render()
        # self.renderwindow_2d.Render()

    def showEvent(self, arg__1: QShowEvent):
        self.wholeExtent = self.Image.GetExtent()
        self.spacing = self.Image.GetSpacing()
        self.label = flip(flip(self.label.transpose(2, 1, 0), 1), 0)
        # d, w, h = self.label.shape
        self.dicom_images_3d.CopyImportVoidPointer(self.label.tostring(), len(self.label.tostring()))
        self.dicom_images_3d.SetDataScalarTypeToUnsignedChar()
        self.dicom_images_3d.SetNumberOfScalarComponents(1)

        self.dicom_images_3d.SetDataSpacing(self.spacing[0], self.spacing[1], self.spacing[2])
        self.dicom_images_3d.SetDataExtent(self.wholeExtent[0], self.wholeExtent[1], self.wholeExtent[2], self.wholeExtent[3], self.wholeExtent[4], self.wholeExtent[5])
        self.dicom_images_3d.SetWholeExtent(self.wholeExtent[0], self.wholeExtent[1], self.wholeExtent[2], self.wholeExtent[3], self.wholeExtent[4], self.wholeExtent[5])
        self.dicom_images_3d.Update()
        self.discrete_marching_cubes_3d = vtkDiscreteMarchingCubes()
        self.discrete_marching_cubes_3d.SetInputConnection(self.dicom_images_3d.GetOutputPort())
        self.discrete_marching_cubes_3d.GenerateValues(3, 1, 3)
        # discrete_marching_cubes.ComputeNormalsOn()
        self.discrete_marching_cubes_3d.Update()

        self.colorLookupTable = vtkLookupTable()
        self.colorLookupTable.SetNumberOfTableValues(3)
        self.colorLookupTable.SetTableValue(0, 204 / 255.0, 84 / 255.0, 58 / 255.0, 1)
        # colorLookupTable.SetTableValue(1, 180/255.0, 160/255.0, 100/255.0, 1)
        self.colorLookupTable.SetTableValue(1, 218 / 255.0, 201 / 255.0, 166 / 255.0, 1)
        self.colorLookupTable.SetTableValue(2, 112 / 255.0, 160 / 255.0, 180 / 255.0, 1)
        self.colorLookupTable.Build()

        # self.image_map_to_color = vtkImageMapToColors()
        # self.image_map_to_color.SetInputConnection(self.dicom_images_3d.GetOutputPort())
        # self.image_map_to_color.SetLookupTable(self.colorLookupTable)
        # self.image_map_to_color.Update()
        #
        # self.image_blender = vtkImageBlend()
        # self.image_blender.AddInputData(self.Image)
        # self.image_blender.AddInputData(self.image_map_to_color.GetOutput())
        # self.image_blender.SetOpacity(0, 1.0)
        # self.image_blender.SetOpacity(1, 1.0)
        # self.image_blender.Update()

        self.dicom_data_mapper_3d = vtkPolyDataMapper()
        self.dicom_data_mapper_3d.SetInputConnection(self.discrete_marching_cubes_3d.GetOutputPort())
        self.dicom_data_mapper_3d.ScalarVisibilityOn()
        self.dicom_data_mapper_3d.SetLookupTable(self.colorLookupTable)
        self.dicom_data_mapper_3d.SetScalarRange(1, 3)
        self.dicom_data_mapper_3d.Update()

        self.actor_dicom_3d = vtkActor()
        self.actor_dicom_3d.SetMapper(self.dicom_data_mapper_3d)
        self.ren_3d.AddActor(self.actor_dicom_3d)

        self.PlaneWidgetY_3d.SetInputData(self.Image)
        self.PlaneWidgetY_3d.SetSliceIndex(self.wholeExtent[2])
        self.PlaneWidgetZ_3d.SetInputData(self.Image)
        self.PlaneWidgetZ_3d.SetSliceIndex(self.wholeExtent[4])
        self.PlaneWidgetY_3d.On()
        self.PlaneWidgetZ_3d.On()

        # self.label_2d = np.zeros_like(self.label)
        # self.label_2d[self.wholeExtent[2], :, :] = self.label[self.wholeExtent[2], :, :]
        # self.dicom_images_2d.CopyImportVoidPointer(self.label_2d.tostring(), len(self.label_2d.tostring()))
        # self.dicom_images_2d.SetDataScalarTypeToUnsignedChar()
        # self.dicom_images_2d.SetNumberOfScalarComponents(1)
        #
        # self.dicom_images_2d.SetDataSpacing(self.spacing[0], self.spacing[1], self.spacing[2])
        # self.dicom_images_2d.SetDataExtent(self.wholeExtent[0], self.wholeExtent[1], self.wholeExtent[2],
        #                                    self.wholeExtent[3], self.wholeExtent[4], self.wholeExtent[5])
        # self.dicom_images_2d.SetWholeExtent(self.wholeExtent[0], self.wholeExtent[1], self.wholeExtent[2],
        #                                     self.wholeExtent[3], self.wholeExtent[4], self.wholeExtent[5])
        # self.dicom_images_2d.Update()
        # self.discrete_marching_cubes_2d = vtkDiscreteMarchingCubes()
        # self.discrete_marching_cubes_2d.SetInputConnection(self.dicom_images_2d.GetOutputPort())
        # self.discrete_marching_cubes_2d.GenerateValues(3, 1, 3)
        # # discrete_marching_cubes.ComputeNormalsOn()
        # self.discrete_marching_cubes_2d.Update()

        # self.image_map_to_color = vtkImageMapToColors()
        # self.image_map_to_color.SetInputConnection(self.dicom_images_3d.GetOutputPort())
        # self.image_map_to_color.SetLookupTable(self.colorLookupTable)
        # self.image_map_to_color.Update()
        #
        # self.image_blender = vtkImageBlend()
        # self.image_blender.AddInputData(self.Image)
        # self.image_blender.AddInputData(self.image_map_to_color.GetOutput())
        # self.image_blender.SetOpacity(0, 1.0)
        # self.image_blender.SetOpacity(1, 1.0)
        # self.image_blender.Update()

        # self.dicom_data_mapper_2d = vtkPolyDataMapper()
        # self.dicom_data_mapper_2d.SetInputConnection(self.discrete_marching_cubes_2d.GetOutputPort())
        # self.dicom_data_mapper_2d.ScalarVisibilityOn()
        # self.dicom_data_mapper_2d.SetLookupTable(self.colorLookupTable)
        # self.dicom_data_mapper_2d.SetScalarRange(1, 3)
        # self.dicom_data_mapper_2d.Update()
        #
        # self.actor_dicom_2d = vtkActor()
        # self.actor_dicom_2d.SetMapper(self.dicom_data_mapper_2d)
        # self.ren_2d.AddActor(self.actor_dicom_2d)
        # self.PlaneWidgetY_2d.SetInputData(self.Image)
        # self.PlaneWidgetY_2d.SetSliceIndex(self.wholeExtent[2])
        # self.PlaneWidgetZ_2d.SetInputData(self.Image)
        # self.PlaneWidgetZ_2d.SetSliceIndex(self.wholeExtent[4])
        # self.PlaneWidgetY_2d.On()
        # self.PlaneWidgetZ_2d.On()

        self.renderwindow_3d.Render()
        self.iren_3d.Initialize()
        # self.renderwindow_2d.Render()
        # self.iren_2d.Initialize()
        self.sliber.setMinimum(0)
        self.sliber.setMaximum(self.wholeExtent[5])
        self.sliber.setValue(self.PlaneWidgetZ_3d.GetSliceIndex())
        self.slice_num_label.setText(str(self.PlaneWidgetZ_3d.GetSliceIndex()))
        arg__1

    def closeEvent(self, arg__1: QCloseEvent):
        self.PlaneWidgetY_3d.Off()
        self.PlaneWidgetZ_3d.Off()
        arg__1
