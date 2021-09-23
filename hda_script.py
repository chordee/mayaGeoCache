
import threading
import numpy as np
import imp
import hou


def cache():
    node = hou.pwd()
    nc = imp.load_source('', node.parm('module_path').eval())
    alt_node = hou.pwd().path() + '/WRITE_OUT'
    geo = hou.node(alt_node).geometry()
    fps = hou.fps()

    start_frame = node.parm('start_frame').eval()
    end_frame = node.parm('end_frame').eval()
    eval_rate = node.parm('eval_rate').eval()
    pname = node.parm('particle_name').eval()

    attrs = [x.name() for x in geo.pointAttribs()]
    xml_path = node.parm('xml').eval()

    xml = nc.NPCacheXML(xml_path)
    xml.setName(pname + 'Shape')
    xml.setFps(fps)
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

    xml.write()

    # Render
    #
    with hou.InterruptableOperation(
            "Cache", "Caching", open_interrupt_dialog=True) as operation:

        threads = []
        for i in range(start_frame, end_frame + 1):
            hou.setFrame(i)

            check_id_attr = geo.findPointAttrib('id')
            if check_id_attr is None:
                hou.ui.displayMessage('Point id attribute not found')
                break

            data_array = _collect_data(geo, attrs)

            mc = nc.NPCacheMC(xml_path)
            mc.setPointArray(data_array)
            mc.setFrame(i)

            th = threading.Thread(target=mc.write)
            th.start()
            threads.append(th)

            operation.updateLongProgress(
                float(i - start_frame) / (end_frame - start_frame),
                "Exporting Frame %d from %d to %d" % (i, start_frame, end_frame)
            )

        for th in threads:
            th.join()


def _collect_data(geo, attrs):
    data_array = []

    # helpers
    def _int_64(attr):
        return geo.pointIntAttribValuesAsString(
            attr, int_type=hou.numericData.Int64
        )

    def _float_32(attr):
        return geo.pointFloatAttribValuesAsString(
            attr
        )

    def _float_64(attr):
        return geo.pointFloatAttribValuesAsString(
            attr, float_type=hou.numericData.Float64
        )

    id_array = np.fromstring(_int_64('id'), dtype=np.int64)
    data_array.append(id_array)

    count_array = np.array([len(geo.points())])
    data_array.append(count_array)

    pos_array = np.fromstring(_float_32('P'), dtype=np.float32).reshape(-1, 3)
    data_array.append(pos_array)

    if 'v' in attrs:
        vel_array = np.fromstring(_float_32('v'), dtype=np.float32).reshape(-1, 3)
        data_array.append(vel_array)

    if 'age' in attrs:
        age_array = np.fromstring(_float_64('age'), dtype=np.float64)
        data_array.append(age_array)

    if 'life' in attrs:
        life_array = np.fromstring(_float_64('life'), dtype=np.float64)
        data_array.append(life_array)

    if 'pscale' in attrs:
        pscale_array = np.fromstring(_float_64('pscale'), dtype=np.float64)
        data_array.append(pscale_array)

    if 'Cd' in attrs:
        cd_array = np.fromstring(_float_32('Cd'), dtype=np.float32).reshape(-1, 3)
        data_array.append(cd_array)

    if 'Alpha' in attrs:
        alpha_array = np.fromstring(_float_64('Alpha'), dtype=np.float64)
        data_array.append(alpha_array)

    if 'rotation' in attrs:
        rotation_array = np.fromstring(_float_32('rotation'), dtype=np.float32).reshape(-1, 3)
        data_array.append(rotation_array)

    return data_array
