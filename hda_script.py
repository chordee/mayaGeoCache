node = hou.pwd()

import sys, threading
import numpy as np
import imp


def cache():
    node = hou.pwd()
    nc = imp.load_source('', node.parm('module_path').eval())
    alt_node = hou.pwd().path() + '/WRITE_OUT'
    geo = hou.node(alt_node).geometry()
    fps = hou.fps()
    timePerFrame = 6000 / fps
    start_frame = node.parm('start_frame').eval()
    end_frame = node.parm('end_frame').eval()
    pname = node.parm('particle_name').eval()

    attrs = [x.name() for x in geo.pointAttribs()]
    xml_path = node.parm('xml').eval()

    xml = nc.NPCacheXML(xml_path)
    xml.setName(pname + 'Shape')

    xml.setStartFrame(start_frame)
    xml.setEndFrame(end_frame)

    if 'v' in attrs:
        xml.appendAttr('velocity', 1)
    if 'age' in attrs:
        xml.appendAttr('age', 0)
    if 'life' in attrs:
        xml.appendAttr('lifespanPP', 0)
    if 'pscale' in attrs:
        xml.appendAttr('radiusPP', 0)
    if 'Cd' in attrs:
        xml.appendAttr('rgbPP', 1)
    if 'Alpha' in attrs:
        xml.appendAttr('opacityPP', 0)
    if 'rotation' in attrs:
        xml.appendAttr('rotationPP', 1)

    xml.setFps(fps)
    xml.write()

    ths = []

    with hou.InterruptableOperation("Cache", "Caching", open_interrupt_dialog=True) as operation:
        for i in range(start_frame, end_frame + 1):
            hou.setFrame(i)
            data_array = []

            check_id_attr = geo.findPointAttrib('id')
            if check_id_attr == None:
                hou.ui.displayMessage('Point id attribute not found')
                break
                return
            id_array = np.fromstring(geo.pointIntAttribValuesAsString('id', int_type=hou.numericData.Int64),
                                     dtype=np.int64)
            data_array.append(id_array)

            count_array = np.array([len(geo.points())])
            data_array.append(count_array)

            pos_array = np.fromstring(geo.pointFloatAttribValuesAsString('P'), dtype=np.float32).reshape(-1, 3)
            data_array.append(pos_array)

            if 'v' in attrs:
                vel_array = np.fromstring(geo.pointFloatAttribValuesAsString('v'), dtype=np.float32).reshape(-1, 3)
                data_array.append(vel_array)

            if 'age' in attrs:
                age_array = np.fromstring(geo.pointFloatAttribValuesAsString('age', float_type=hou.numericData.Float64),
                                          dtype=np.float64)
                data_array.append(age_array)

            if 'life' in attrs:
                life_array = np.fromstring(
                    geo.pointFloatAttribValuesAsString('life', float_type=hou.numericData.Float64), dtype=np.float64)
                data_array.append(life_array)

            if 'pscale' in attrs:
                pscale_array = np.fromstring(
                    geo.pointFloatAttribValuesAsString('pscale', float_type=hou.numericData.Float64), dtype=np.float64)
                data_array.append(pscale_array)

            if 'Cd' in attrs:
                cd_array = np.fromstring(geo.pointFloatAttribValuesAsString('Cd'), dtype=np.float32).reshape(-1, 3)
                data_array.append(cd_array)

            if 'Alpha' in attrs:
                alpha_array = np.fromstring(
                    geo.pointFloatAttribValuesAsString('Alpha', float_type=hou.numericData.Float64), dtype=np.float64)
                data_array.append(alpha_array)

            if 'rotation' in attrs:
                rotation_array = np.fromstring(geo.pointFloatAttribValuesAsString('rotation'),
                                               dtype=np.float32).reshape(-1, 3)
                data_array.append(rotation_array)

            mc = nc.NPCacheMC(xml_path)

            mc.setPointArray(data_array)

            mc.setFrame(i)
            th = threading.Thread(target=mc.write)
            th.start()
            ths.append(th)
            operation.updateLongProgress(float(i - start_frame) / (end_frame - start_frame),
                                         "Exporting Frame %d from %d to %d" % (i, start_frame, end_frame))
        for th in ths:
            th.join()
