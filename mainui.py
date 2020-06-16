import sys
import os
import PySide2

dirname = os.path.dirname(PySide2.__file__)
plugin_path = os.path.join(dirname, 'plugins')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
from vtk import vtkImageViewer2, vtkRenderer, vtkDICOMImageReader, vtkImageData, VTK_FLOAT, vtkImageFlip
from PySide2.QtWidgets import QMainWindow, QPushButton, QFrame, QVBoxLayout, QHBoxLayout, QFileDialog, QApplication, \
    QMessageBox, QLineEdit, QLabel, QSlider, QTextBrowser, QWidget, QRadioButton
from PySide2.QtCore import Slot, QDir, Qt
from PySide2.QtGui import QTextCursor
from vtk.qt4.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util import numpy_support
from vesselfit import get_vessel
from SimpleITK import ImageSeriesReader, GetImageFromArray, IntensityWindowingImageFilter, GetArrayFromImage, LabelOverlay, LabelContour
from cv2 import namedWindow, WINDOW_GUI_NORMAL, createTrackbar, getTrackbarPos,imshow, waitKey, destroyAllWindows
from numpy import zeros, float32, flip, array, uint8, savetxt
from subprocess import Popen
from copy import deepcopy
from get_point import GetPointWindow
from show_result import ShowResultWindow


class MainWindow(QMainWindow):

    def __init__(self, parent=None, argv=None):
        # 主窗体初始化###
        QMainWindow.__init__(self, parent)
        self.setWindowTitle("股浅动脉钙化分型软件")
        self.setMinimumSize(1080, 720)
        self.embedded_dir_flag = False
        self.dir_path = None
        self.save_path = ""
        if len(argv) >= 3:
            self.dir_path = argv[1]
            if len(self.dir_path) > 0:
                self.embedded_dir_flag = True
            self.save_path = argv[2]
            if len(self.save_path) > 0:
                if not os.path.exists(self.save_path):
                    os.makedirs(self.save_path)
        # 打开DICOM文件夹按钮###
        self.open_directory_button = QPushButton("打开文件夹")
        self.open_directory_button.clicked.connect(self.open_directory_button_clicked)
        self.button_font = self.open_directory_button.font()
        self.button_font.setPointSize(14)
        self.open_directory_button.setFont(self.button_font)
        # 路径框###
        self.path_edit = QLineEdit(self)
        # 滑块###
        self.sliber = QSlider()
        self.sliber.setEnabled(False)
        # self.sliber.setVisible(False)
        self.sliber.setOrientation(Qt.Horizontal)
        self.sliber.valueChanged.connect(self.sliber_value_changed)
        # slice计数标签
        self.slice_num_label = QLineEdit(self)
        self.slice_num_label.setAlignment(Qt.AlignCenter)
        self.slice_num_label.setFixedWidth(90)
        label_font = self.slice_num_label.font()
        label_font.setPointSize(18)
        self.slice_num_label.setFont(label_font)
        self.slice_num_label.returnPressed.connect(self.slice_jump_button_clicked)
        # slice跳转按钮
        self.slice_jump_button = QPushButton("跳转")
        self.slice_jump_button.setFixedWidth(90)
        self.slice_jump_button.clicked.connect(self.slice_jump_button_clicked)
        self.slice_jump_button.setFont(self.button_font)
        # dicom-VTK显示控件###
        self.frame = QWidget(self)
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        self.vtkWidget.GlobalWarningDisplayOff()
        self.vtkWidget.setMinimumSize(768, 512)
        self.imageviewer = vtkImageViewer2()
        # self.imageviewer = vtk.vtkImagePlaneWidget()
        self.ren = vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        # 灰度值显示标签###
        self.value_name_label = QLabel("灰度值：")
        self.value_name_label.setFont(label_font)
        self.value_name_label.setFixedHeight(30)
        self.value_label = QLabel("无")
        self.value_label.setFont(label_font)
        self.value_label.setFixedHeight(30)
        # patch-VTK显示控件###
        self.frame_1 = QFrame()
        self.patch_viewer = QVTKRenderWindowInteractor(self.frame)
        self.patch_viewer.GlobalWarningDisplayOff()
        self.patch_viewer.setMinimumSize(256, 256)
        self.patch_viewer.setMaximumSize(512, 512)
        self.imageviewer_1 = vtkImageViewer2()
        self.ren_1 = vtkRenderer()
        self.patch_viewer.GetRenderWindow().AddRenderer(self.ren_1)
        self.iren_1 = self.patch_viewer.GetRenderWindow().GetInteractor()
        # 选腿控件###
        self.left_button = QRadioButton('l')
        self.right_button = QRadioButton('r')
        self.left_button.setFont(self.button_font)
        self.right_button.setFont(self.button_font)
        self.right_button.setChecked(True)
        self.left_button.clicked.connect(self.select_leg_button_clicked)
        self.right_button.clicked.connect(self.select_leg_button_clicked)
        # 分割阈值调整区###
        self.UpperThreshold_label = QLabel("阈值上限：")
        self.UpperThreshold_label.setFont(self.button_font)
        self.UpperThreshold_edit = QLineEdit("1000")
        self.UpperThreshold_edit.setFont(self.button_font)
        self.LowerThreshold_label = QLabel("阈值下限：")
        self.LowerThreshold_label.setFont(self.button_font)
        self.LowerThreshold_edit = QLineEdit("100")
        self.LowerThreshold_edit.setFont(self.button_font)
        # 选取非闭塞段端点按钮###
        self.non_occluded_button = QPushButton("选取非闭塞段端点")
        self.non_occluded_button.clicked.connect(self.non_occluded_button_clicked)
        self.non_occluded_button.setEnabled(False)
        self.non_occluded_button.setFont(self.button_font)
        # 提取非闭塞段血管按钮###
        self.get_non_occluded_button = QPushButton("提取非闭塞段血管")
        self.get_non_occluded_button.clicked.connect(self.get_non_occluded_button_clicked)
        self.get_non_occluded_button.setEnabled(False)
        self.get_non_occluded_button.setFont(self.button_font)
        # 选取闭塞段控制点按钮###
        self.occluded_button = QPushButton("选取闭塞段控制点")
        self.occluded_button.clicked.connect(self.occluded_button_clicked)
        self.occluded_button.setEnabled(False)
        self.occluded_button.setFont(self.button_font)
        # 提取血管按钮###
        self.get_vessel_button = QPushButton("提取血管")
        self.get_vessel_button.clicked.connect(self.get_vessel_button_clicked)
        self.get_vessel_button.setEnabled(False)
        self.get_vessel_button.setFont(self.button_font)
        # 结果展示按钮###
        self.show_2D_result_button = QPushButton("显示提取结果（二维）")
        self.show_2D_result_button.clicked.connect(self.show_2D_result_button_clicked)
        self.show_2D_result_button.setEnabled(False)
        # self.show_2D_result_button.setVisible(False)
        self.show_2D_result_button.setFont(self.button_font)
        self.show_3D_result_button = QPushButton("显示提取结果（三维）")
        self.show_3D_result_button.clicked.connect(self.show_3D_result_button_clicked)
        self.show_3D_result_button.setEnabled(False)
        # self.show_3D_result_button.setVisible(False)
        self.show_3D_result_button.setFont(self.button_font)
        ###patch保存按钮###
        self.save_patch_button = QPushButton("保存patch")
        self.save_patch_button.clicked.connect(self.save_patch_button_clicked)
        self.save_patch_button.setEnabled(False)
        # self.save_patch_button.setVisible(False)
        self.save_patch_button.setFont(self.button_font)
        ###分型按钮###
        self.decide_type_button = QPushButton("进行分型")
        self.decide_type_button.clicked.connect(self.decide_type_button_clicked)
        self.decide_type_button.setEnabled(False)
        # self.decide_type_button.setVisible(False)
        self.decide_type_button.setFont(self.button_font)
        ###信息框###
        self.info_browser = QTextBrowser()
        self.info_browser.setFont(self.button_font)
        self.info_browser.setMaximumHeight(100)
        self.info_browser.textChanged.connect(self.info_browser_text_changed)
        ###路径布局###
        self.path_layout = QHBoxLayout()
        self.path_layout.addWidget(self.path_edit)
        self.path_layout.addWidget(self.open_directory_button)
        # sliber标签布局
        self.sliber_layout = QHBoxLayout()
        # self.sliber_layout.setSpacing(500)
        self.sliber_layout.setAlignment(Qt.AlignCenter)
        self.sliber_layout.addWidget(self.slice_num_label)
        self.sliber_layout.addWidget(self.slice_jump_button)
        ###选腿按钮布局###
        self.select_leg_layout = QHBoxLayout()
        self.select_leg_layout.addWidget(self.left_button)
        self.select_leg_layout.addWidget(self.right_button)
        ###阈值调整区布局###
        self.UpperThreshold_layout = QHBoxLayout()
        self.UpperThreshold_layout.addWidget(self.UpperThreshold_label)
        self.UpperThreshold_layout.addWidget(self.UpperThreshold_edit)
        self.LowerThreshold_layout = QHBoxLayout()
        self.LowerThreshold_layout.addWidget(self.LowerThreshold_label)
        self.LowerThreshold_layout.addWidget(self.LowerThreshold_edit)
        self.Threshold_layout = QHBoxLayout()
        self.Threshold_layout.addLayout(self.UpperThreshold_layout)
        self.Threshold_layout.addLayout(self.LowerThreshold_layout)
        ###灰度值标签布局###
        self.value_layout = QHBoxLayout()
        self.value_layout.addWidget(self.value_name_label)
        self.value_layout.addWidget(self.value_label)
        ###patch分型显示布局###
        self.patch_type_layout = QVBoxLayout()
        self.patch_type_layout.setAlignment(Qt.AlignCenter)
        self.patch_type_layout.addLayout(self.value_layout)
        self.patch_type_layout.addWidget(self.patch_viewer, Qt.AlignCenter)
        self.patch_type_layout.addLayout(self.select_leg_layout)
        self.patch_type_layout.addLayout(self.Threshold_layout)
        ###显示控件布局###
        self.viewer_layout = QHBoxLayout()
        self.viewer_layout.setAlignment(Qt.AlignCenter)
        self.viewer_layout.addWidget(self.vtkWidget)
        self.viewer_layout.addLayout(self.patch_type_layout)
        ###功能按钮布局###
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.non_occluded_button)
        self.button_layout.addWidget(self.get_non_occluded_button)
        self.button_layout.addWidget(self.occluded_button)
        self.button_layout.addWidget(self.get_vessel_button)
        self.button_layout.addWidget(self.show_2D_result_button)
        self.button_layout.addWidget(self.show_3D_result_button)
        self.button_layout.addWidget(self.save_patch_button)
        self.button_layout.addWidget(self.decide_type_button)
        ###主布局###
        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(self.path_layout)
        # self.main_layout.addWidget(self.slice_num_label)
        self.main_layout.addLayout(self.sliber_layout)
        self.main_layout.addWidget(self.sliber)
        # self.main_layout.addWidget(self.vtkWidget)
        self.main_layout.addLayout(self.viewer_layout)
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addWidget(self.info_browser)
        # self.LastPickedActor = None
        # self.LastPickedProperty = vtk.vtkProperty()

        self.dicomreader = vtkDICOMImageReader()
        # self.ren.ResetCamera()
        self.frame.setLayout(self.main_layout)
        self.setCentralWidget(self.frame)
        # self.frame_1.setLayout(self.main_layout)
        # self.setCentralWidget(self.frame_1)

        self.iren.Initialize()
        self.iren_1.Initialize()
        self.dir_name = None
        self.dcm = None
        self.spacing = []
        self.all_data_set = []
        self.UpperThreshold = int(self.UpperThreshold_edit.text())
        self.LowerThreshold = int(self.LowerThreshold_edit.text())
        self.seedname = 'right leg'
        self.seedpt = None
        self.seedpt_list = []
        self.get_non_occluded_flag = False
        self.seed_slice = 0
        self.seedpt3d_list = []
        self.end_points = []
        self.flag = False
        self.l_center = []
        self.r_center = []
        self.center = []
        self.vessel_center = []
        self.vessel_flag = True
        self.dim = 0
        self.image_data = None
        self.numpy_label = zeros(self.dim, dtype=float32)
        self.non_occluded_numpy_label = zeros(self.dim, dtype=float32)
        self.patch_data = []
        self.txt_patch_data = []
        self.patch_image = vtkImageData()
        self.patch_flag = False
        self.label_all = []
        self.conf_all = []
        self.right_labels = []
        self.slice_number = 0
        self.show()
        if self.embedded_dir_flag:
            self.open_directory_button_clicked()

    ###打开文件夹按钮功能函数###
    def open_directory_button_clicked(self):
        if not self.embedded_dir_flag:
            self.dir_path = QFileDialog.getExistingDirectory(self, "DICOM文件夹", '\home',
                                                         QFileDialog.ShowDirsOnly)
        while len(self.dir_path) > 0:
            tempdir = QDir(self.dir_path)
            self.dir_name = tempdir.dirName()
            allfile = tempdir.entryList(filters=QDir.Files)

            if len(allfile) <= 100:
                msgbtn = QMessageBox.warning(self, "警告", "文件夹中数量过少，是否重新选择？\n文件路径:" + self.dir_path,
                                             QMessageBox.Ok | QMessageBox.Cancel)
                if msgbtn == QMessageBox.Ok:
                    self.dir_path = QFileDialog.getExistingDirectory(self, "DICOM文件夹", '\home',
                                                                     QFileDialog.ShowDirsOnly)
                else:
                    break
            else:
                break
        if len(self.dir_path) > 0:
            # a = time.time()
            self.path_edit.setText(self.dir_path)
            self.info_browser.insertPlainText("数据读取中......\n")
            self.repaint()
            self.dicomreader.SetDirectoryName(self.dir_path)
            self.dicomreader.Update()
            self.imageviewer.SetInputConnection(self.dicomreader.GetOutputPort())
            self.imageviewer.SetupInteractor(self.iren)
            self.imageviewer.SetRenderWindow(self.vtkWidget.GetRenderWindow())
            self.iren.RemoveObservers('MouseWheelBackwardEvent')
            self.iren.RemoveObservers('MouseWheelForwardEvent')
            # self.iren.AddObserver('LeftButtonPressEvent', self.left_pressed)
            self.iren.AddObserver('MouseMoveEvent', self.mouse_move)
            self.iren.AddObserver('MouseWheelBackwardEvent', self.last_slice)
            self.iren.AddObserver('MouseWheelForwardEvent', self.next_slice)
            self.ren.ResetCamera()
            self.ren_1.ResetCamera()
            self.iren.Initialize()
            self.iren.Start()
            self.imageviewer.Render()
            self.imageviewer.SetSlice(0)
            # self.imageviewer.SetSize(512, 512)
            self.slice_num_label.setText(str(self.imageviewer.GetSlice()))
            self.sliber.setMaximum(self.imageviewer.GetSliceMax())
            self.sliber.setMinimum(self.imageviewer.GetSliceMin())
            self.sliber.setValue(self.imageviewer.GetSlice())
            self.slice_number = self.imageviewer.GetSlice()
            self.dim = self.dicomreader.GetOutput().GetDimensions()
            self.spacing = self.dicomreader.GetOutput().GetSpacing()
            self.image_data = numpy_support.vtk_to_numpy(self.dicomreader.GetOutput().GetPointData().GetScalars())
            self.image_data = self.image_data.reshape(self.dim[2], self.dim[1], self.dim[0])
            self.image_data = flip(flip(self.image_data, axis=1), axis=0)
            reader = ImageSeriesReader()
            filenamesDICOM = reader.GetGDCMSeriesFileNames(self.dir_path)
            reader.SetFileNames(filenamesDICOM)
            reader.LoadPrivateTagsOn()
            self.dcm = reader.Execute()
            self.sliber.setEnabled(True)
            self.sliber.setVisible(True)
            self.non_occluded_button.setEnabled(True)
            self.occluded_button.setEnabled(True)
            self.show_2D_result_button.setEnabled(False)
            self.show_3D_result_button.setEnabled(False)
            self.save_patch_button.setEnabled(False)
            self.patch_flag = False
            self.get_non_occluded_button.setEnabled(False)
            self.center = []
            self.l_center = []
            self.r_center = []
            self.vessel_center = []
            self.end_points = []
            self.seed_slice = 0
            self.seedpt3d_list = []
            self.numpy_label = zeros(0)
            self.non_occluded_numpy_label = zeros(0)
            self.patch_data = []
            self.txt_patch_data = []
            self.patch_image = vtkImageData()
            self.get_non_occluded_flag = False
            self.get_vessel_button.setEnabled(False)
            self.decide_type_button.setEnabled(False)
            # self.all_data_set = None
            # self.all_data_set = []
            # for file_name in allfile:
            #     file_path = os.path.join(self.dir_path, file_name)
            #     data_set = pydicom.dcmread(file_path)
            #     self.all_data_set.append(data_set)
            self.info_browser.insertPlainText("数据读取完成！\n")
            self.embedded_dir_flag = False
            # print(time.time() - a)

    # 滚轮向上滚动功能函数
    def last_slice(self, obj, ev):
        self.imageviewer.SetSlice((self.slice_number - 1) % self.imageviewer.GetSliceMax())
        if self.patch_flag:
            self.imageviewer_1.SetSlice((self.slice_number - 1) % self.imageviewer_1.GetSliceMax())
        self.slice_num_label.setText(str(self.imageviewer.GetSlice()))
        self.sliber.setValue(self.slice_number - 1)

    # 滚轮向下滚动功能函数
    def next_slice(self, obj, ev):
        self.imageviewer.SetSlice((self.slice_number + 1) % self.imageviewer.GetSliceMax())
        if self.patch_flag:
            self.imageviewer_1.SetSlice((self.slice_number + 1) % self.imageviewer_1.GetSliceMax())
        self.slice_num_label.setText(str(self.imageviewer.GetSlice()))
        self.sliber.setValue(self.slice_number + 1)

    def slice_jump_button_clicked(self):
        self.slice_number = int(self.slice_num_label.text()) % self.imageviewer.GetSliceMax()
        self.imageviewer.SetSlice(self.slice_number)
        if self.patch_flag:
            self.imageviewer_1.SetSlice(self.slice_number % self.imageviewer_1.GetSliceMax())
        self.sliber.setValue(self.slice_number)

    def mouse_move(self, obj, ev):
        position = self.iren.GetEventPosition()
        self.imageviewer.GetRenderer().SetDisplayPoint(position[0], position[1], 0)
        self.imageviewer.GetRenderer().DisplayToWorld()
        world_position = self.imageviewer.GetRenderer().GetWorldPoint()
        bounds = self.imageviewer.GetImageActor().GetBounds()
        if 0 <= world_position[0] <= bounds[1] and 0 <= world_position[1] <= bounds[3]:
            index_x = round(world_position[0] / self.spacing[0])
            index_y = round(world_position[1] / self.spacing[1])
            # image_data = np.flip(np.flip(self.image_data_data, axis=1), axis=2).transpose(2, 1, 0)
            value = self.image_data[self.imageviewer.GetSliceMax() - self.imageviewer.GetSlice(), self.image_data.shape[
                2] - index_y - 1, index_x]
            self.value_label.setText("(" + str(index_x) + "," + str(self.dim[1] - 1 - index_y) + ")" + str(value))

    # 选腿按钮功能函数
    # @Slot()
    def select_leg_button_clicked(self):
        self.repaint()
        button = self.sender()
        if button.text() == 'l':
            self.seedname = 'left leg'
        if button.text() == 'r':
            self.seedname = 'right leg'

    # 非闭塞段端点按钮功能函数
    @Slot()
    def non_occluded_button_clicked(self):
        self.flag = False
        self.end_points = self.vtk_get_point(title="非闭塞段选点")
        if len(self.end_points) >= 2:
            self.get_vessel_button.setEnabled(True)
            self.get_non_occluded_flag = False
            self.get_non_occluded_button.setEnabled(True)
            self.show_2D_result_button.setEnabled(False)
            self.show_3D_result_button.setEnabled(False)
            self.save_patch_button.setEnabled(False)
            self.decide_type_button.setEnabled(False)
            self.patch_flag = False
            sourcepoints = []
            targetpoints = []
            for i in range(len(self.end_points)):
                if i % 2 == 0:
                    sourcepoints.append(self.end_points[i])
                else:
                    if self.end_points[i][2] < self.end_points[i - 1][2]:
                        targetpoints.append(self.end_points[i - 1])
                        sourcepoints[-1] = self.end_points[i]
                    else:
                        targetpoints.append(self.end_points[i])
            for i in range(len(sourcepoints) - 1):
                deltaz = sourcepoints[i + 1][2] - targetpoints[i][2]
                if deltaz > 20:
                    self.info_browser.insertPlainText(
                        "建议在{}和{}间选取{}个控制点\n".format(targetpoints[i][2], sourcepoints[i + 1][2], int(deltaz / 20)))

    # 提取非闭塞段血管按钮
    @Slot()
    def get_non_occluded_button_clicked(self):
        self.get_non_occluded_flag = False
        self.info_browser.insertPlainText("非闭塞段血管提取中...\n")
        self.repaint()
        # a = time.time()
        self.non_occluded_numpy_label = zeros(self.dim, dtype=float32)
        self.numpy_label = zeros(self.dim, dtype=float32)
        self.UpperThreshold = int(self.UpperThreshold_edit.text())
        self.LowerThreshold = int(self.LowerThreshold_edit.text())
        self.vessel_flag = True
        self.numpy_label = get_vessel(self, interplot=False)
        if self.vessel_flag:
            self.non_occluded_numpy_label = self.non_occluded_numpy_label + self.numpy_label
            # print(time.time() - a)
            self.get_non_occluded_flag = True
            self.show_2D_result_button.setEnabled(True)
            self.show_3D_result_button.setEnabled(True)
            self.show_2D_result_button.setVisible(True)
            self.show_3D_result_button.setVisible(True)
            image = GetImageFromArray(self.image_data)
            filter_intensity = IntensityWindowingImageFilter()
            filter_intensity.SetOutputMaximum(255)
            filter_intensity.SetOutputMinimum(0)
            filter_intensity.SetWindowMinimum(-200)
            filter_intensity.SetWindowMaximum(900)
            image = filter_intensity.Execute(image)
            image_data = GetArrayFromImage(image)
            image_data = image_data.transpose(2, 1, 0)
            box_height = 32
            box_width = 32
            self.patch_data = zeros([box_height * 2, box_width * 2, self.dim[2]], dtype=float32)
            real_center = array(self.vessel_center).astype(float32)
            i = 0
            for center in self.vessel_center:
                point = self.dcm.TransformIndexToPhysicalPoint(center)
                real_center[i, 0] = point[0]
                real_center[i, 1] = point[1]
                real_center[i, 2] = point[2]
                i = i + 1
            if self.seedname == 'right leg':
                self.r_center = real_center
            if self.seedname == 'left leg':
                self.l_center = real_center
            for center in self.vessel_center:
                slice_num = center[2]
                img_slice = image_data[:, :, slice_num]
                patch_slice = img_slice[center[0] - box_height + 1: center[0] + box_height + 1,
                              center[1] - box_width + 1: center[1] + box_width + 1]
                self.patch_data[:, :, slice_num] = patch_slice
            image = GetImageFromArray(self.image_data)
            image_data = GetArrayFromImage(image)
            image_data = image_data.transpose(2, 1, 0)
            self.txt_patch_data = zeros([box_height * 2, box_width * 2, self.dim[2]], dtype=float32)
            for center in self.vessel_center:
                slice_num = center[2]
                img_slice = image_data[:, :, slice_num]
                patch_slice = img_slice[center[0] - box_height + 1: center[0] + box_height + 1,
                              center[1] - box_width + 1: center[1] + box_width + 1]
                self.txt_patch_data[:, :, slice_num] = patch_slice

            vtk_data_array = numpy_support.numpy_to_vtk(
                flip(flip(self.txt_patch_data, axis=1), axis=2).transpose(2, 1, 0).ravel(), deep=True,
                array_type=VTK_FLOAT)
            self.patch_image = vtkImageData()
            self.patch_image.SetDimensions(box_height * 2, box_width * 2, self.dim[2])
            self.patch_image.GetPointData().SetScalars(vtk_data_array)
            self.imageviewer_1.SetInputData(self.dicomreader.GetOutput())
            self.imageviewer_1.SetupInteractor(self.iren_1)
            self.imageviewer_1.SetRenderWindow(self.patch_viewer.GetRenderWindow())
            self.ren_1.ResetCameraClippingRange()
            self.iren_1.Initialize()
            self.iren_1.Start()
            self.imageviewer_1.Render()
            self.imageviewer_1.SetInputData(self.patch_image)
            self.imageviewer_1.SetupInteractor(self.iren_1)
            self.imageviewer_1.SetRenderWindow(self.patch_viewer.GetRenderWindow())
            # self.imageviewer_1.SetSize(256, 256)
            self.ren_1.ResetCamera()
            self.iren_1.Initialize()
            self.iren_1.Start()
            self.imageviewer_1.Render()
            self.patch_flag = True
            self.save_patch_button.setEnabled(True)
            self.decide_type_button.setEnabled(False)
            # self.decide_type_button.setEnabled(True)
            self.get_non_occluded_flag = True
            self.info_browser.insertPlainText("非闭塞段血管提取完成！可拖动滑块在小窗口中查看patch\n")

    # 滑块功能函数
    @Slot()
    def sliber_value_changed(self):
        self.slice_number = self.sliber.value()
        self.imageviewer.SetSlice(self.slice_number)
        self.slice_num_label.setText(str(self.slice_number))
        if self.patch_flag:
            self.imageviewer_1.SetSlice(self.slice_number)

    # opencv实现选点
    def on_trace_bar_changed(self, args):
        pass

    # 闭塞段控制点按钮功能函数
    @Slot()
    def occluded_button_clicked(self):
        self.flag = True
        # self.center = []
        # self.capture_mouse(self.image_data)
        self.center = self.vtk_get_point(title="闭塞段选点")
        if len(self.center) > 2:
            self.get_vessel_button.setEnabled(True)
            self.show_2D_result_button.setEnabled(False)
            self.show_3D_result_button.setEnabled(False)
            self.save_patch_button.setEnabled(False)
            self.decide_type_button.setEnabled(False)
            self.patch_flag = False
            self.flag = False

    # 提取血管按钮功能函数
    def get_vessel_button_clicked(self):
        self.vessel_center = []
        self.info_browser.insertPlainText("血管提取中......\n")
        self.repaint()
        self.numpy_label = zeros(self.dim, dtype=float32)
        if self.get_non_occluded_flag:
            self.numpy_label = self.numpy_label + self.non_occluded_numpy_label
        self.UpperThreshold = int(self.UpperThreshold_edit.text())
        self.LowerThreshold = int(self.LowerThreshold_edit.text())
        self.vessel_flag = True
        self.numpy_label = get_vessel(self)
        if self.vessel_flag:
            self.show_2D_result_button.setEnabled(True)
            self.show_3D_result_button.setEnabled(True)
            image = GetImageFromArray(self.image_data)
            filter_intensity = IntensityWindowingImageFilter()
            filter_intensity.SetOutputMaximum(255)
            filter_intensity.SetOutputMinimum(0)
            filter_intensity.SetWindowMinimum(-200)
            filter_intensity.SetWindowMaximum(900)
            image = filter_intensity.Execute(image)
            image_data = GetArrayFromImage(image)
            image_data = image_data.transpose(2, 1, 0)
            box_height = 32
            box_width = 32
            self.patch_data = zeros([box_height * 2, box_width * 2, self.dim[2]], dtype=float32)
            real_center = array(self.vessel_center).astype(float)
            i = 0
            for center in self.vessel_center:
                point = self.dcm.TransformIndexToPhysicalPoint(center)
                real_center[i, 0] = point[0]
                real_center[i, 1] = point[1]
                real_center[i, 2] = point[2]
                i = i + 1
            if self.seedname == 'right leg':
                self.r_center = real_center
            if self.seedname == 'left leg':
                self.l_center = real_center
            for center in self.vessel_center:
                slice_num = center[2]
                img_slice = image_data[:, :, slice_num]
                patch_slice = img_slice[center[0] - box_height + 1: center[0] + box_height + 1,
                              center[1] - box_width + 1: center[1] + box_width + 1]
                self.patch_data[:, :, slice_num] = patch_slice
            image = GetImageFromArray(self.image_data)
            image_data = GetArrayFromImage(image)
            image_data = image_data.transpose(2, 1, 0)
            self.txt_patch_data = zeros([box_height * 2, box_width * 2, self.dim[2]], dtype=float32)
            for center in self.vessel_center:
                slice_num = center[2]
                img_slice = image_data[:, :, slice_num]
                patch_slice = img_slice[center[0] - box_height + 1: center[0] + box_height + 1,
                              center[1] - box_width + 1: center[1] + box_width + 1]
                self.txt_patch_data[:, :, slice_num] = patch_slice
            vtk_data_array = numpy_support.numpy_to_vtk(
                flip(flip(self.txt_patch_data, axis=1), axis=2).transpose(2, 1, 0).ravel(), deep=True,
                array_type=VTK_FLOAT)
            self.patch_image = vtkImageData()
            self.patch_image.SetDimensions(box_height * 2, box_width * 2, self.dim[2])
            self.patch_image.GetPointData().SetScalars(vtk_data_array)
            self.imageviewer_1.SetInputData(self.dicomreader.GetOutput())
            self.imageviewer_1.SetupInteractor(self.iren_1)
            self.imageviewer_1.SetRenderWindow(self.patch_viewer.GetRenderWindow())
            self.ren_1.ResetCameraClippingRange()
            self.iren_1.Initialize()
            self.iren_1.Start()
            self.imageviewer_1.Render()
            self.imageviewer_1.SetInputData(self.patch_image)
            self.imageviewer_1.SetupInteractor(self.iren_1)
            self.imageviewer_1.SetRenderWindow(self.patch_viewer.GetRenderWindow())
            # self.imageviewer_1.SetSize(256, 256)
            self.ren_1.ResetCamera()
            self.iren_1.Initialize()
            self.iren_1.Start()
            self.imageviewer_1.Render()
            self.patch_flag = True
            self.save_patch_button.setEnabled(True)
            self.decide_type_button.setEnabled(False)
            # self.decide_type_button.setEnabled(True)
            self.info_browser.insertPlainText("血管提取完成！可拖动滑块在小窗口中查看patch。\n")

    # 结果展示按钮功能函数
    @Slot()
    def show_3D_result_button_clicked(self):
        # a = time.time()
        self.display3d()
        # print(time.time() - a)

    def display3d(self):
        # label = deepcopy(self.numpy_label.astype(np.uint8))
        # label = np.flip(np.flip(label.transpose(2, 1, 0), 1), 0)
        # d, w, h = label.shape
        # dicom_images = vtkImageImport()
        # dicom_images.CopyImportVoidPointer(label.tostring(), len(label.tostring()))
        # dicom_images.SetDataScalarTypeToUnsignedChar()
        # dicom_images.SetNumberOfScalarComponents(1)
        #
        # dicom_images.SetDataSpacing(self.spacing[0], self.spacing[1], self.spacing[2])
        # dicom_images.SetDataExtent(0, h - 1, 0, w - 1, 0, d - 1)
        # dicom_images.SetWholeExtent(0, h - 1, 0, w - 1, 0, d - 1)
        # dicom_images.Update()
        #
        # # render = vtkRenderer()
        # # render_window = vtkRenderWindow()
        # # render_window.SetSize(1280, 800)
        # # render_window.AddRenderer(render)
        # # self.vtkWidget.GetRenderWindow().AddRenderer(render)
        # # render_interact = vtkRenderWindowInteractor()
        # # render_interact.SetRenderWindow(render_window)
        # # render_interact.SetRenderWindow(self.vtkWidget.GetRenderWindow())
        #
        # # threshold_dicom_image = vtk.vtkImageThreshold()
        # # threshold_dicom_image.SetInputConnection(dicom_images.GetOutputPort())
        # # threshold_dicom_image.Update()
        #
        # discrete_marching_cubes = vtkDiscreteMarchingCubes()
        # discrete_marching_cubes.SetInputConnection(dicom_images.GetOutputPort())
        # discrete_marching_cubes.GenerateValues(3, 1, 3)
        # # discrete_marching_cubes.ComputeNormalsOn()
        # discrete_marching_cubes.Update()
        #
        # colorLookupTable = vtkLookupTable()
        # colorLookupTable.SetNumberOfTableValues(3)
        # colorLookupTable.Build()
        # colorLookupTable.SetTableValue(0, 204 / 255.0, 84 / 255.0, 58 / 255.0, 1)
        # # colorLookupTable.SetTableValue(1, 180/255.0, 160/255.0, 100/255.0, 1)
        # colorLookupTable.SetTableValue(1, 218 / 255.0, 201 / 255.0, 166 / 255.0, 1)
        # colorLookupTable.SetTableValue(2, 112 / 255.0, 160 / 255.0, 180 / 255.0, 1)
        #
        # dicom_data_mapper = vtkPolyDataMapper()
        # dicom_data_mapper.SetInputConnection(discrete_marching_cubes.GetOutputPort())
        # dicom_data_mapper.ScalarVisibilityOn()
        # dicom_data_mapper.SetLookupTable(colorLookupTable)
        # dicom_data_mapper.SetScalarRange(1, 3)
        # dicom_data_mapper.Update()
        #
        # actor_dicom_3d = vtkActor()
        # actor_dicom_3d.SetMapper(dicom_data_mapper)

        # render.AddActor(actor_dicom_3d)
        a = ShowResultWindow()
        a.setWindowTitle("提取结果")
        # a.ren_3d.AddActor(actor_dicom_3d)
        a.Image = self.imageviewer.GetInput()
        a.label = deepcopy(self.numpy_label.astype(uint8))
        a.show()
        # render.ResetCamera()
        # self.ren.AddActor(actor_dicom_3d)
        # self.ren.ResetCamera()

        # render_window.Render()
        # self.vtkWidget.GetRenderWindow().Render()
        # render_interact.Start()

    def show_2D_result_button_clicked(self):
        self.slice_seg_contours()

    def slice_seg_contours(self, planes='t'):
        img = GetImageFromArray(self.image_data)
        label = GetImageFromArray(uint8(self.numpy_label.transpose(2, 1, 0)))
        label.CopyInformation(img)
        h, w, s = img.GetSize()
        filter_intensity = IntensityWindowingImageFilter()
        namedWindow('Segmentation(exit with \'Q\')', WINDOW_GUI_NORMAL)
        createTrackbar('Slice', 'Segmentation(exit with \'Q\')', 0, s - 1, self.on_trace_bar_changed)
        filter_intensity.SetOutputMaximum(255)
        filter_intensity.SetOutputMinimum(0)
        filter_intensity.SetWindowMinimum(-200)
        filter_intensity.SetWindowMaximum(900)
        img_show = filter_intensity.Execute(img)
        while True:
            slice_num = getTrackbarPos('Slice', 'Segmentation(exit with \'Q\')')
            if planes == 't':
                itk_display = LabelOverlay(img_show[:, :, slice_num], LabelContour(label[:, :, slice_num]),
                                                1.0)
            elif planes == 's':
                itk_display = LabelOverlay(img_show[:, slice_num, :], LabelContour(label[:, slice_num, :]),
                                                1.0)
            elif planes == 'c':
                itk_display = LabelOverlay(img_show[slice_num, :, :], LabelContour(label[slice_num, :, :]),
                                                1.0)
            else:
                break

            img_display = GetArrayFromImage(itk_display)
            imshow('Segmentation(exit with \'Q\')', uint8(img_display))
            if 0xFF & waitKey(10) == ord('q'):
                destroyAllWindows()
                break

    def show_2d_result(self):
        pass

    # patch保存按钮功能函数###
    @Slot()
    def save_patch_button_clicked(self):
        save_path = QFileDialog.getExistingDirectory(self, "保存路径", self.save_path, QFileDialog.ShowDirsOnly)
        if len(save_path) > 0:
            self.info_browser.insertPlainText("pactch保存中...\n")
            self.repaint()
            if self.seedname == 'left leg':
                leg = 'l'
            if self.seedname == 'right leg':
                leg = 'r'
            # patch_dir = os.path.join(save_path, self.dir_name + "_jpeg")
            # if not os.path.exists(patch_dir):
            #     os.makedirs(patch_dir)
            # for center in self.vessel_center:
            #     slice_num = center[2]
            #     patch_img_name = "{}_{}.jpeg".format(leg, slice_num)
            #     patch_path = os.path.join(patch_dir, patch_img_name)
            #     cv.imwrite(patch_path, np.uint8(self.patch_data[:, :, slice_num]))
            # self.info_browser.insertPlainText("patch保存至" + patch_dir + "完成!\n")
            patch_dir = os.path.join(save_path, self.dir_name + "_txt")
            if not os.path.exists(patch_dir):
                os.makedirs(patch_dir)
            for center in self.vessel_center:
                slice_num = center[2]
                patch_img_name = "{}_{}.txt".format(leg, slice_num)
                patch_path = os.path.join(patch_dir, patch_img_name)
                savetxt(patch_path, self.txt_patch_data[:, :, slice_num], fmt='%d', delimiter=' ')
            self.info_browser.insertPlainText("patch保存至" + patch_dir + "完成!\n")
            # patch_dir = os.path.join(save_path, self.dir_name + "_dicom")
            # if not os.path.exists(patch_dir):
            #     os.makedirs(patch_dir)
            # slice_max = self.imageviewer.GetSliceMax()
            # for slice_num in range(slice_max + 1):
            #     slice_data = np.where(self.numpy_label[:, :, slice_max - slice_num] > 0, 1025, 0)
            #     slice_data = np.transpose(slice_data)
            #     self.all_data_set[slice_num].PixelData = slice_data.astype(np.int16).tobytes()
            #     patch_img_name = "{}_{}".format(leg, slice_num)
            #     patch_path = os.path.join(patch_dir, patch_img_name)
            #     self.all_data_set[slice_num].save_as(patch_path)
            # self.info_browser.insertPlainText("patch保存至" + patch_dir + "完成!\n")
            # patch_dir = os.path.join(save_path, self.dir_name + ".nii")
            # slice_data = np.where(self.numpy_label > 0, self.numpy_label, 0)
            # slice_data = np.flip(slice_data, axis=2)
            # slice_data = np.transpose(slice_data, (2, 1, 0)).astype(np.uint8)
            # seg = sitk.GetImageFromArray(slice_data)
            # seg.CopyInformation(self.dcm)
            # seg.SetOrigin(self.dcm.GetOrigin())
            # seg.SetSpacing(self.dcm.GetSpacing())
            # seg.SetDirection(self.dcm.GetDirection())
            # sitk.WriteImage(seg, patch_dir, True)
            self.info_browser.insertPlainText("patch保存至" + patch_dir + "完成!\n")
            # patch_dir = save_path + '/' + self.dir_name + "_" + leg + "_center.txt"
            # real_center = np.concatenate((np.array(self.l_center), np.array(self.r_center)))
            # np.savetxt(patch_dir, real_center, fmt='%f', delimiter=' ')
            self.decide_type_button.setEnabled(True)

    ###分型按钮功能函数###
    @Slot()
    def decide_type_button_clicked(self):
        # os.system("./typeui/typeui.exe")
        # os.system(os.path.dirname(os.path.realpath(__file__)) + "\\typeui\\typeui.exe")
        self.info_browser.insertPlainText(os.path.dirname(os.path.realpath(__file__)) + "\\typeui\\typeui.exe")
        Popen(os.path.dirname(os.path.realpath(__file__)) + "\\typeui\\typeui.exe")

    ###信息框自动滚动###
    @Slot()
    def info_browser_text_changed(self):
        self.vtkWidget.GetRenderWindow().Finalize()
        self.info_browser.moveCursor(QTextCursor().End)

    ###vtk选点###
    def vtk_get_point(self, title="选点"):
        get_point_widget = GetPointWindow(selected_points=self.end_points)
        get_point_widget.setWindowTitle(title)
        get_point_widget.setWindowFlag(Qt.WindowMaximizeButtonHint)
        get_point_widget.setWindowFlag(Qt.WindowMinimizeButtonHint)
        flip = vtkImageFlip()
        flip.SetInputData(self.dicomreader.GetOutput())
        flip.SetFilteredAxis(2)
        flip.Update()
        get_point_widget.Image = flip.GetOutput()
        # get_point_widget.open()
        # if get_point_widget.exec() == QDialog.Accepted:
        get_point_widget.exec()
        return get_point_widget.point_list


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("windowsxp")
    window = MainWindow(argv=sys.argv)
    sys.exit(app.exec_())
