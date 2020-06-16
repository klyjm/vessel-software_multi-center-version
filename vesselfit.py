# import os
from vmtk import vmtkscripts
# import SimpleITK as sitk
# import cv2 as cv
# import numpy as np
from numpy import flip, argwhere, mean, asarray, squeeze, c_
from vtk import vtkExtractVOI, vtkImageThreshold, vtkImageData,vtkSeedWidget
from vtk.util import numpy_support
from interp import interp1
from copy import deepcopy


def sort2(s):
    return s[2]


def get_vessel(window, interplot=True):
    points = deepcopy(window.end_points)
    numpy_label = deepcopy(window.numpy_label)
    dim = deepcopy(window.dim)
    imageport = window.dicomreader.GetOutputPort()
    sourcepoints = []
    targetpoints = []
    if len(points) >= 2:
        points.sort(key=sort2)
        for i in range(len(points)):
            if i % 2 == 0:
                sourcepoints.append(points[i])
            else:
                targetpoints.append(points[i])
        if not window.get_non_occluded_flag:
            for i in range(len(sourcepoints)):
                vmtkImageInitialization = vmtkscripts.vmtkImageInitialization()
                vmtkImageInitialization.Interactive = 0
                evoi = vtkExtractVOI()
                evoi.SetInputConnection(imageport)
                evoi.SetVOI(0, dim[0] - 1, 0, dim[1] - 1, min(dim[2] - sourcepoints[i][2] - 1, dim[2] - targetpoints[i][2] - 1), max(dim[2] - sourcepoints[i][2] - 1, dim[2] - targetpoints[i][2] - 1))
                evoi.Update()
                voiimage = evoi.GetOutput()
                vmtkImageInitialization.Image = voiimage
                vmtkImageInitialization.UpperThreshold = window.UpperThreshold
                vmtkImageInitialization.LowerThreshold = window.LowerThreshold
                vmtkImageInitialization.NegateImage = 0
                # vmtkImageInitialization.SourcePoints = [sourcepoints[i][0], dim[1] - sourcepoints[i][1] - 1,
                #                                         dim[2] - sourcepoints[i][2] - 1]
                # vmtkImageInitialization.TargetPoints = [targetpoints[i][0], dim[1] - targetpoints[i][1] - 1,
                #                                         dim[2] - targetpoints[i][2] - 1]
                vmtkImageInitialization.SourcePoints = [sourcepoints[i][0], sourcepoints[i][1],
                                                        dim[2] - sourcepoints[i][2] - 1]
                vmtkImageInitialization.TargetPoints = [targetpoints[i][0], targetpoints[i][1],
                                                        dim[2] - targetpoints[i][2] - 1]
                vmtkImageInitialization.Execute()

                # Feature Image
                imageFeatures = vmtkscripts.vmtkImageFeatures()
                imageFeatures.Image = voiimage
                imageFeatures.FeatureImageType = 'upwind'
                imageFeatures.SigmoidRemapping = 0
                imageFeatures.DerivativeSigma = 0.0
                imageFeatures.UpwindFactor = 1.0
                imageFeatures.FWHMRadius = [1.0, 1.0, 1.0]
                imageFeatures.FWHMBackgroundValue = 0.0
                imageFeatures.Execute()

                # # Level Sets
                levelset = vmtkscripts.vmtkLevelSetSegmentation()
                levelset.Image = voiimage
                levelset.LevelSetsInput = vmtkImageInitialization.InitialLevelSets
                levelset.FeatureImage = imageFeatures.FeatureImage
                levelset.IsoSurfaceValue = 0.0
                levelset.LevelSetEvolution()

                # convert to Numpy data
                threshold = vtkImageThreshold()
                threshold.SetInputData(levelset.LevelSetsOutput)
                threshold.ThresholdByLower(0)
                threshold.ReplaceInOn()
                threshold.ReplaceOutOn()
                threshold.SetOutValue(0)
                threshold.SetInValue(1)
                threshold.Update()

                outVolumeData = vtkImageData()
                outVolumeData.DeepCopy(threshold.GetOutput())
                temp_label = numpy_support.vtk_to_numpy(outVolumeData.GetPointData().GetScalars())
                temp_label = temp_label.reshape(abs(sourcepoints[i][2] - targetpoints[i][2]) + 1, dim[1], dim[0])
                temp_label = temp_label.transpose(2, 1, 0)
                temp_label = flip(flip(temp_label, axis=1), axis=2)
                numpy_label[:, :, min(sourcepoints[i][2], targetpoints[i][2]):(max(sourcepoints[i][2], targetpoints[i][2]) + 1)] = numpy_label[:, :, min(sourcepoints[i][2], targetpoints[i][2]):(max(sourcepoints[i][2], targetpoints[i][2]) + 1)] + temp_label
    labelindex = argwhere(numpy_label == 1)
    control_points = deepcopy(window.center)
    if labelindex.shape[0] + len(control_points) <= 3:
        window.vessel_flag = False
        window.info_browser.insertPlainText("血管提取失败！请查看设置是否正确。\n")
        return numpy_label
    for point in control_points:
        point[1] = dim[1] - 1 - point[1]
    pointsz = [temp[2] for temp in control_points]
    for centerpoint in points:
        if centerpoint[2] not in pointsz:
            # control_points.append(centerpoint)
            control_points.append([centerpoint[0], dim[1] - 1 - centerpoint[1], centerpoint[2]])
    pointsz = [temp[2] for temp in control_points]
    for i in range(dim[2]):
        if i not in pointsz:
            temp = labelindex[argwhere(labelindex[:, 2] == i), :]
            if temp.shape[0] >= 1:
                centerpoint = mean(temp, axis=0)
                control_points.append([int(centerpoint[0, 0]), int(centerpoint[0, 1]), int(centerpoint[0, 2])])
    control_points.sort(key=sort2)
    # numpy_label = np.flip(numpy_label, axis=1)
    if interplot:
        x = [temp[0] for temp in control_points]
        y = [temp[1] for temp in control_points]
        z = [temp[2] for temp in control_points]
        interpz = list(range(min(z), max(z) + 1))
        interpx, interpy = interp1(x, y, z, interpz)
        for i in range(len(interpz)):
            window.vessel_center.append([int(interpx[i]), int(interpy[i]), int(interpz[i])])
        # for i in range(len(interpz)):
        #     numpy_label[int(interpx[i]), int(interpy[i]), int(interpz[i])] = 1
        # plt.figure()
        # plt.subplot(121)
        # plt.plot(interpz, interpx, 'o')
        # plt.subplot(122)
        # plt.plot(interpz, interpy, 'o')
        # plt.show()

        if len(sourcepoints) >= 1:
            if len(sourcepoints) > 1:
                for i in range(1, len(sourcepoints)):
                    sourcepoint = asarray(sourcepoints[i])
                    targetpoint = asarray(targetpoints[i - 1])
                    deltaceter = sourcepoint - targetpoint
                    deltaz = deltaceter[2]
                    temp = squeeze(
                        labelindex[argwhere(labelindex[:, 2] == targetpoint[2] - int(deltaz / abs(deltaz))), :])
                    tz = targetpoint[2] - int(deltaz / abs(deltaz))
                    while len(temp) <= 0:
                        temp = squeeze(labelindex[argwhere(labelindex[:, 2] == tz), :])
                        tz = tz - int(deltaz / abs(deltaz))
                    targetpoint = mean(temp, axis=0)
                    temp = temp[:, 0:2]
                    sourcecircle = squeeze(
                        labelindex[argwhere(labelindex[:, 2] == sourcepoint[2] + int(deltaz / abs(deltaz))), :])
                    sz = sourcepoint[2] + int(deltaz / abs(deltaz))
                    while len(sourcecircle) <= 0:
                        sourcecircle = squeeze(labelindex[argwhere(labelindex[:, 2] == sz), :])
                        sz = sz + int(deltaz / abs(deltaz))
                    sourcepoint = mean(sourcecircle, axis=0)
                    sourcecircle = sourcecircle[:, 0:2]
                    deltaceter = sourcepoint - targetpoint
                    deltaz = deltaceter[2]
                    deltaceter = deltaceter[0:2]
                    targetcircle = temp + deltaceter
                    targetpointzindex = interpz.index(targetpoint[2])
                    sourcepointzindex = interpz.index(sourcepoint[2])
                    for j in range(len(targetcircle)):
                        d = []
                        for k in range(len(sourcecircle)):
                            d.append((abs(targetcircle[j, 0] - sourcecircle[k, 0]) ** 2 + abs(
                                targetcircle[j, 1] - sourcecircle[k, 1]) ** 2) ** 0.5)
                        mind = min(d)
                        min_index = d.index(mind)
                        nearestpoint = sourcecircle[min_index, :]
                        delta = nearestpoint - targetcircle[j, :]
                        for k in range(1, int(abs(deltaz))):
                            temppoint = delta * (k / abs(deltaz)) + targetcircle[j, :]
                            realk = int(round(k / deltaz * abs(deltaz)))
                            realpoint = temppoint - (sourcepoint[0:2] - asarray(
                                [interpx[targetpointzindex + realk], interpy[targetpointzindex + realk]]))
                            numpy_label[int(realpoint[0]), int(realpoint[1]), interpz[targetpointzindex + realk]] = 2
                targetpoint = targetpoints[0]
                sourcepoint = sourcepoints[0]
                if targetpoint[-1] > sourcepoint[-1]:
                    targetpoint = targetpoints[-1]
                else:
                    sourcepoint = sourcepoints[-1]
                targetpoint = asarray(targetpoint)
                targetpoint = targetpoint.squeeze()
                sourcepoint = asarray(sourcepoint)
                sourcepoint = sourcepoint.squeeze()
            elif len(sourcepoints) == 1:
                targetpoint = asarray(targetpoints)
                targetpoint = targetpoint.squeeze()
                sourcepoint = asarray(sourcepoints)
                sourcepoint = sourcepoint.squeeze()
            deltaceter = sourcepoint - targetpoint
            deltaz = deltaceter[2]
            targetcircle = squeeze(
                labelindex[argwhere(labelindex[:, 2] == targetpoint[2] + int(deltaz / abs(deltaz))), :])
            tz = targetpoint[2] + int(deltaz / abs(deltaz))
            while len(targetcircle) <= 0:
                tz = tz + int(deltaz / abs(deltaz))
                targetcircle = squeeze(
                    labelindex[argwhere(labelindex[:, 2] == tz), :])
            targetpoint = mean(targetcircle, axis=0)
            targetcircle = targetcircle[:, 0:2]
            sourcecircle = squeeze(
                labelindex[argwhere(labelindex[:, 2] == sourcepoint[2] - int(deltaz / abs(deltaz))), :])
            sz = sourcepoint[2] - int(deltaz / abs(deltaz))
            while len(sourcecircle) <= 0:
                sz = sz - int(deltaz / abs(deltaz))
                sourcecircle = squeeze(
                    labelindex[argwhere(labelindex[:, 2] == sz), :])
            sourcepoint = mean(sourcecircle, axis=0)
            sourcecircle = sourcecircle[:, 0:2]
            targetpointzindex = interpz.index(targetpoint[2])
            sourcepointzindex = interpz.index(sourcepoint[2])
            if targetpointzindex > sourcepointzindex:
                for i in range(sourcepointzindex):
                    delta = asarray([interpx[i], interpy[i]]) - sourcepoint[0:2]
                    realcircle = sourcecircle + delta
                    for j in range(len(realcircle)):
                        numpy_label[int(realcircle[j, 0]), int(realcircle[j, 1]), interpz[i]] = 2
                for i in range(targetpointzindex + 1, len(interpz)):
                    delta = asarray([interpx[i], interpy[i]]) - targetpoint[0:2]
                    realcircle = targetcircle + delta
                    for j in range(len(realcircle)):
                        numpy_label[int(realcircle[j, 0]), int(realcircle[j, 1]), interpz[i]] = 2
            else:
                for i in range(targetpointzindex):
                    delta = asarray([interpx[i], interpy[i]]) - targetpoint[0:2]
                    realcircle = targetcircle + delta
                    for j in range(len(realcircle)):
                        numpy_label[int(realcircle[j, 0]), int(realcircle[j, 1]), interpz[i]] = 2
                for i in range(sourcepointzindex + 1, len(interpz)):
                    delta = asarray([interpx[i], interpy[i]]) - sourcepoint[0:2]
                    realcircle = sourcecircle + delta
                    for j in range(len(realcircle)):
                        numpy_label[int(realcircle[j, 0]), int(realcircle[j, 1]), interpz[i]] = 2
        else:
            circle = asarray(
                [[0, 3], [0, 2], [0, 4], [1, 1], [1, 5], [2, 1], [2, 5], [3, 0], [3, 6], [4, 1], [4, 5], [5, 1],
                 [5, 5], [6, 3], [6, 2], [6, 4]])
            for i in range(len(interpz)):
                delta = c_[interpx[i], interpy[i]] - [3, 3]
                realcircle = circle + delta
                for j in range(len(circle)):
                    numpy_label[int(realcircle[j, 0]), int(realcircle[j, 1]), interpz[i]] = 2
    else:
        for i in range(len(control_points)):
            window.vessel_center.append([int(control_points[i][0]), int(control_points[i][1]), int(control_points[i][2])])
    # numpy_label = np.flip(numpy_label, axis=1)
    return numpy_label



