#coding:GBK
from PySide2.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QTextBrowser, QPushButton, QLineEdit, QSpacerItem, QSizePolicy
from PySide2.QtGui import QShowEvent, QCloseEvent, Qt
from vtk.qt4.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk import vtkImagePlaneWidget, vtkImageData, vtkGlyph3D, vtkSphereSource, vtkRenderer, vtkCellPicker, vtkPolyData, vtkPolyDataMapper, vtkActor, vtkPoints, vtkInteractorStyleTrackballCamera, vtkTextActor, vtkCamera


class GetPointWindow(QDialog):

    def __init__(self, parent=None, selected_points=None):
        QDialog.__init__(self, parent)
        self.vtkwidget = QVTKRenderWindowInteractor(self)
        self.vtkwidget.GlobalWarningDisplayOff()
        self.vtkwidget.setMinimumSize(720, 720)
        self.Image = vtkImageData()
        self.renderwindow = self.vtkwidget.GetRenderWindow()
        self.iren = self.renderwindow.GetInteractor()
        self.ren = vtkRenderer()
        self.renderwindow.AddRenderer(self.ren)
        self.TextureInterpolation = 1
        ###����###
        self.sliber = QSlider()
        self.sliber.setOrientation(Qt.Horizontal)
        self.sliber.valueChanged.connect(self.sliber_value_changed)
        ###slice������ǩ###
        self.slice_num_label = QLineEdit(self)
        self.slice_num_label.setAlignment(Qt.AlignCenter)
        self.slice_num_label.setFixedWidth(90)
        label_font = self.slice_num_label.font()
        label_font.setPointSize(16)
        self.slice_num_label.setFont(label_font)
        self.slice_num_label.returnPressed.connect(self.slice_jump_button_clicked)
        # slice��ת��ť
        self.slice_jump_button = QPushButton("��ת")
        self.slice_jump_button.setFixedWidth(90)
        self.slice_jump_button.clicked.connect(self.slice_jump_button_clicked)
        self.slice_jump_button.setFont(label_font)
        ###ѡ�����###
        self.get_point_introduction_name_label = QLabel("����˵��")
        self.get_point_introduction_name_label.setFont(label_font)
        self.get_point_introduction_label = QLabel("��ͼ���У�\nCtrl+����Ҽ�/�м���ѡ��\nShift+����Ҽ�/�м���ȡ����ǰ��Ƭѡ��\n��ͼ���⣺\n���������Ŵ�/��С\n����Ҽ�����ת\n����м���ƽ��")
        self.get_point_introduction_label.setFont(label_font)
        # �ӽ�ѡ�ť
        self.reset_button = QPushButton("�����ӽ�")
        self.reset_button.setFont(label_font)
        self.reset_button.clicked.connect(self.reset_button_clicked)
        self.zoom_amplify_button = QPushButton("�Ŵ�")
        self.zoom_amplify_button.setFont(label_font)
        self.zoom_amplify_button.clicked.connect(self.zoom_amplify_button_clicked)
        self.zoom_shrink_button = QPushButton("��С")
        self.zoom_shrink_button.setFont(label_font)
        self.zoom_shrink_button.clicked.connect(self.zoom_shrink_button_clicked)
        ###�����Ϣ��###
        self.point_display_browser_name_label = QLabel("�����Ϣ:")
        self.point_display_browser_name_label.setFont(label_font)
        self.point_display_browser = QTextBrowser()
        self.point_display_browser.setFont(label_font)
        # �ѱ����Ϣ��
        self.selected_point_display_browser_name_label = QLabel("��ѡ�㣺")
        self.selected_point_display_browser_name_label.setFont(label_font)
        self.selected_point_display_browser = QTextBrowser()
        self.selected_point_display_browser.setText(str(selected_points).replace('[','').replace(']',''))
        self.selected_point_display_browser.setFont(label_font)
        # �˳���ť
        self.ok_button = QPushButton("ȷ��")
        self.ok_button.setFont(label_font)
        self.ok_button.clicked.connect(self.ok_button_clicked)
        self.cancel_button = QPushButton("ȡ��")
        self.cancel_button.setFont(label_font)
        self.cancel_button.clicked.connect(self.cancel_button_clicked)
        # slice��ǩ����
        self.slice_label_layout = QHBoxLayout()
        self.left_spacer = QSpacerItem(10, 40, hData=QSizePolicy.Expanding)
        self.slice_label_layout.addItem(self.left_spacer)
        self.slice_label_layout.addWidget(self.slice_num_label)
        self.right_spacer = QSpacerItem(10, 40, hData=QSizePolicy.Expanding)
        self.slice_label_layout.addItem(self.right_spacer)
        self.slice_label_layout.addWidget(self.slice_jump_button)
        ###�����Ϣ����###
        self.sub_layout = QHBoxLayout()
        self.sub_layout.addWidget(self.point_display_browser_name_label)
        self.sub_layout.addWidget(self.reset_button)
        self.sub_layout.addWidget(self.zoom_amplify_button)
        self.sub_layout.addWidget(self.zoom_shrink_button)
        self.point_display_layout = QVBoxLayout()
        self.point_display_layout.addLayout(self.sub_layout)
        self.point_display_layout.addWidget(self.point_display_browser)
        self.point_display_layout.addWidget(self.selected_point_display_browser_name_label)
        self.point_display_layout.addWidget(self.selected_point_display_browser)
        self.point_display_layout.addWidget(self.get_point_introduction_name_label)
        self.point_display_layout.addWidget(self.get_point_introduction_label)
        # �˳���ť����
        self.exit_layout = QHBoxLayout()
        self.exit_layout.addWidget(self.ok_button)
        self.exit_layout.addWidget(self.cancel_button)
        # �Ҳ಼��
        self.right_layout = QVBoxLayout()
        self.right_layout.addLayout(self.point_display_layout)
        self.right_layout.addLayout(self.exit_layout)
        # ѡ��ؼ�����/��಼��###
        self.get_point_layout = QVBoxLayout()
        # self.get_point_layout.addWidget(self.slice_num_label)
        self.get_point_layout.addLayout(self.slice_label_layout)
        self.get_point_layout.addWidget(self.sliber)
        self.get_point_layout.addWidget(self.vtkwidget)
        ###������###
        self.main_layout = QHBoxLayout()
        self.main_layout.addLayout(self.get_point_layout)
        self.main_layout.addLayout(self.right_layout)
        self.setLayout(self.main_layout)

        ###�����ʼ��###
        self.iren.SetInteractorStyle(vtkInteractorStyleTrackballCamera())
        self.iren.GetInteractorStyle().KeyPressActivationOff()
        self.iren.GetInteractorStyle().AddObserver("MouseWheelBackwardEvent", self.last_slice)
        self.iren.GetInteractorStyle().AddObserver("MouseWheelForwardEvent", self.next_slice)
        self.PlaneWidgetY = vtkImagePlaneWidget()
        self.PlaneWidgetY.SetInteractor(self.iren)
        self.Picker = vtkCellPicker()
        self.Picker.SetTolerance(0.005)
        self.PlaneWidgetZ = vtkImagePlaneWidget()
        self.PlaneWidgetZ.SetInteractor(self.iren)
        self.PlaneWidgetZ.AddObserver("StartInteractionEvent", self.AddSeed)
        self.PlaneWidgetZ.SetPicker(self.Picker)
        self.Seeds = vtkPolyData()
        self.InitializeSeeds()
        self.PlaneWidgetY.SetResliceInterpolateToLinear()
        self.PlaneWidgetY.SetTextureInterpolate(self.TextureInterpolation)
        self.PlaneWidgetY.SetPlaneOrientationToYAxes()
        self.PlaneWidgetY.DisplayTextOff()
        self.PlaneWidgetY.KeyPressActivationOff()
        self.PlaneWidgetY.InteractionOff()
        self.PlaneWidgetZ.SetResliceInterpolateToLinear()
        self.PlaneWidgetZ.SetTextureInterpolate(self.TextureInterpolation)
        self.PlaneWidgetZ.SetPlaneOrientationToZAxes()
        self.PlaneWidgetZ.DisplayTextOn()
        self.PlaneWidgetZ.KeyPressActivationOff()
        self.PlaneWidgetZ.SetLeftButtonAction(self.PlaneWidgetZ.VTK_WINDOW_LEVEL_ACTION)
        self.PlaneWidgetZ.SetRightButtonAction(self.PlaneWidgetZ.VTK_CURSOR_ACTION)
        self.PlaneWidgetZ.SetMiddleButtonAction(self.PlaneWidgetZ.VTK_CURSOR_ACTION)
        self.TextActor = vtkTextActor()

        ###���ݳ�ʼ��###
        self.wholeExtent = []
        self.point_list = []
        self.point_z = []
        self.slice_number = 0
        self.init_position = (0.0, 0.0, 0.0)

    def reset_button_clicked(self):
        # camera = vtkCamera()
        camera = self.ren.GetActiveCamera()
        self.ren.ResetCamera()
        camera.SetPosition(self.init_position[0], self.init_position[1], self.init_position[2])
        camera.SetViewUp(0, 1, 0)
        self.renderwindow.Render()

    def zoom_amplify_button_clicked(self):
        self.ren.GetActiveCamera().Zoom(1.1)
        self.renderwindow.Render()
        # self.ren.GetActiveCamera().SetParallelScale(self.ren.GetActiveCamera().GetParallelScale() * 1.1)

    def zoom_shrink_button_clicked(self):
        self.ren.GetActiveCamera().Zoom(0.9)
        self.renderwindow.Render()
        # self.ren.GetActiveCamera().SetParallelScale(self.ren.GetActiveCamera().GetParallelScale() * 0.9)

    def sliber_value_changed(self):
        self.PlaneWidgetZ.SetSliceIndex(self.sliber.value())
        self.slice_num_label.setText(str(self.PlaneWidgetZ.GetSliceIndex()))
        self.slice_number = self.sliber.value()
        self.renderwindow.Render()

    def slice_jump_button_clicked(self):
        self.slice_number = int(self.slice_num_label.text()) % self.wholeExtent[5]
        self.PlaneWidgetZ.SetSliceIndex(self.slice_number)
        self.sliber.setValue(self.slice_number)

    def AddSeed(self, obj, event):
        if self.iren.GetControlKey():
            cursorData = [0.0, 0.0, 0.0, 0.0]
            obj.GetCursorData(cursorData)
            spacing = self.Image.GetSpacing()
            origin = self.Image.GetOrigin()
            point = [0.0,0.0,0.0]
            point[0] = cursorData[0] * spacing[0] + origin[0]
            point[1] = cursorData[1] * spacing[1] + origin[1]
            point[2] = cursorData[2] * spacing[2] + origin[2]
            if point[2] not in self.point_z:
                self.point_z.append(point[2])
                self.Seeds.GetPoints().InsertNextPoint(point)
                self.point_list.append([int(cursorData[0]), int(cursorData[1]), int(cursorData[2])])
            else:
                deleteid = self.point_z.index(point[2])
                new_points = vtkPoints()
                for i in range(self.Seeds.GetPoints().GetNumberOfPoints()):
                    if i != deleteid:
                        new_points.InsertNextPoint(self.Seeds.GetPoints().GetPoint(i))
                    else:
                        new_points.InsertNextPoint(point)
                        self.point_list[i] = [int(cursorData[0]), int(cursorData[1]), int(cursorData[2])]
                self.Seeds.SetPoints(new_points)
            self.point_display_browser.setText(str(self.point_list))
            self.Seeds.Modified()
            self.renderwindow.Render()
        elif self.iren.GetShiftKey():
            cursorData = [0.0, 0.0, 0.0, 0.0]
            obj.GetCursorData(cursorData)
            spacing = self.Image.GetSpacing()
            origin = self.Image.GetOrigin()
            point_z = cursorData[2] * spacing[2] + origin[2]
            if point_z in self.point_z:
                deleteid = self.point_z.index(point_z)
                new_points = vtkPoints()
                for i in range(self.Seeds.GetPoints().GetNumberOfPoints()):
                    if i != deleteid:
                        new_points.InsertNextPoint(self.Seeds.GetPoints().GetPoint(i))
                self.Seeds.SetPoints(new_points)
                self.point_z.pop(deleteid)
                self.point_list.pop(deleteid)
                self.point_display_browser.setText(str(self.point_list).replace('[', '').replace(']', ''))
            self.Seeds.Modified()
            self.renderwindow.Render()

    def last_slice(self, obj, ev):
        self.PlaneWidgetZ.SetSliceIndex((self.slice_number - 1) % self.wholeExtent[5])
        self.slice_num_label.setText(str(self.PlaneWidgetZ.GetSliceIndex()))
        self.sliber.setValue(self.PlaneWidgetZ.GetSliceIndex())
        self.slice_number = self.PlaneWidgetZ.GetSliceIndex()
        self.renderwindow.Render()

    def next_slice(self, obj, ev):
        self.PlaneWidgetZ.SetSliceIndex((self.slice_number + 1) % self.wholeExtent[5])
        self.slice_num_label.setText(str(self.PlaneWidgetZ.GetSliceIndex()))
        self.sliber.setValue(self.PlaneWidgetZ.GetSliceIndex())
        self.slice_number = self.PlaneWidgetZ.GetSliceIndex()
        self.renderwindow.Render()

    def InitializeSeeds(self):
        self.Seeds.Initialize()
        seedPoints = vtkPoints()
        self.Seeds.SetPoints(seedPoints)

    def showEvent(self, arg__1: QShowEvent):
        # self.iren.SetInteractorStyle(vtkInteractorStyleTrackballCamera())
        # self.iren.GetInteractorStyle().KeyPressActivationOff()
        # self.iren.GetInteractorStyle().AddObserver("MouseWheelBackwardEvent", self.last_slice)
        # self.iren.GetInteractorStyle().AddObserver("MouseWheelForwardEvent", self.next_slice)
        # self.iren.AddObserver("MouseMoveEvent", self.AddSeed)
        # self.iren.AddObserver('LeftButtonPressEvent', self.AddSeed)
        # self.iren.GetInteractorStyle().AddObserver("CharEvent", self.vmtkRenderer.CharCallback)
        # self.iren.GetInteractorStyle().AddObserver("KeyPressEvent", self.vmtkRenderer.KeyPressCallback)

        ##self.PrintLog('Ctrl +  left click to add seed.')
        # PlaneWidgetX = vtk.vtkImagePlaneWidget()
        # PlaneWidgetX.SetInteractor(vmtkRenderer.RenderWindowInteractor)
        # PlaneWidgetX.AddObserver("StartInteractionEvent", AddSeed)
        # PlaneWidgetX.SetPicker(Picker)
        # self.PlaneWidgetY = vtkImagePlaneWidget()
        # self.PlaneWidgetY.SetInteractor(self.iren)
        # self.PlaneWidgetY.AddObserver("StartInteractionEvent", self.AddSeed)
        # self.PlaneWidgetY.SetPicker(self.Picker)
        # self.Picker = vtkCellPicker()
        # self.Picker.SetTolerance(0.005)
        # self.PlaneWidgetZ = vtkImagePlaneWidget()
        # self.PlaneWidgetZ.SetInteractor(self.iren)
        # self.PlaneWidgetZ.AddObserver("StartInteractionEvent", self.AddSeed)
        # self.PlaneWidgetZ.AddObserver("MouseMoveEvent", self.AddSeed)
        # self.PlaneWidgetZ.SetPicker(self.Picker)

        # self.InitializeSeeds()
        # self.Seeds.GetPoints().SetNumberOfPoints(1)

        self.wholeExtent = self.Image.GetExtent()
        # PlaneWidgetX.SetResliceInterpolateToLinear()
        # PlaneWidgetX.SetTextureInterpolate(TextureInterpolation)
        # PlaneWidgetX.SetInputData(Image)
        # PlaneWidgetX.SetPlaneOrientationToXAxes()
        # PlaneWidgetX.SetSliceIndex(wholeExtent[0])
        # PlaneWidgetX.DisplayTextOff()
        # PlaneWidgetX.KeyPressActivationOff()

        # self.PlaneWidgetY.SetResliceInterpolateToLinear()
        # self.PlaneWidgetY.SetTextureInterpolate(self.TextureInterpolation)
        self.PlaneWidgetY.SetInputData(self.Image)
        # self.PlaneWidgetY.SetPlaneOrientationToYAxes()
        self.PlaneWidgetY.SetSliceIndex(self.wholeExtent[2])
        # self.PlaneWidgetY.DisplayTextOff()
        # self.PlaneWidgetY.KeyPressActivationOff()
        # self.PlaneWidgetY.InteractionOff()
        # PlaneWidgetY.SetLookupTable(PlaneWidgetX.GetLookupTable())
        # self.PlaneWidgetZ.SetResliceInterpolateToLinear()
        # self.PlaneWidgetZ.SetTextureInterpolate(self.TextureInterpolation)
        self.PlaneWidgetZ.SetInputData(self.Image)
        # self.PlaneWidgetZ.SetPlaneOrientationToZAxes()
        self.PlaneWidgetZ.SetSliceIndex(self.wholeExtent[4])
        # self.PlaneWidgetZ.DisplayTextOn()
        # self.PlaneWidgetZ.KeyPressActivationOff()
        # self.PlaneWidgetZ.SetLeftButtonAction(self.PlaneWidgetZ.VTK_WINDOW_LEVEL_ACTION)
        # self.PlaneWidgetZ.SetRightButtonAction(self.PlaneWidgetZ.VTK_CURSOR_ACTION)
        # self.PlaneWidgetZ.SetMiddleButtonAction(self.PlaneWidgetZ.VTK_CURSOR_ACTION)
        glyphs = vtkGlyph3D()
        glyphSource = vtkSphereSource()
        glyphs.SetInputData(self.Seeds)
        glyphs.SetSourceConnection(glyphSource.GetOutputPort())
        # glyphs.SetScaleModeToDataScalingOff()
        glyphs.SetScaleModeToScaleByVector()
        glyphs.SetScaleFactor(self.Image.GetLength() * 0.003)
        glyphMapper = vtkPolyDataMapper()
        glyphMapper.SetInputConnection(glyphs.GetOutputPort())
        self.SeedActor = vtkActor()
        self.SeedActor.SetMapper(glyphMapper)
        self.SeedActor.GetProperty().SetColor(1.0, 0.0, 0.0)
        self.ren.AddActor(self.SeedActor)
        self.ren.AddActor(self.TextActor)
        self.PlaneWidgetY.On()
        self.PlaneWidgetZ.On()

        self.renderwindow.Render()
        self.iren.Initialize()
        self.sliber.setMinimum(0)
        self.sliber.setMaximum(self.wholeExtent[5])
        self.sliber.setValue(self.PlaneWidgetZ.GetSliceIndex())
        self.slice_num_label.setText(str(self.PlaneWidgetZ.GetSliceIndex()))
        self.slice_number = self.PlaneWidgetZ.GetSliceIndex()
        self.ren.ResetCamera()
        camera = self.ren.GetActiveCamera()
        self.init_position = camera.GetPosition()
        arg__1


    def ok_button_clicked(self):
        self.close()


    def cancel_button_clicked(self):
        self.point_list = []
        self.close()

    def closeEvent(self, arg__1: QCloseEvent):
        self.PlaneWidgetY.Off()
        self.PlaneWidgetZ.Off()
        arg__1
