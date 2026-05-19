# mayaGeoCache I/O

Python classes for reading and writing Maya Geometry Cache and nParticle
Cache files, plus a Houdini HDA wrapper for exporting nParticle caches from
a Houdini point geometry sequence.

Only the **One File Per Frame** layout is supported. Both Geometry Cache and
nParticle Cache depend on the XML description file, so any write path must
start by producing a valid XML through the `NCacheXML` / `NPCacheXML`
classes.

The binary layout follows the public reverse-engineered nCache bitstream
spec by 100cells (Maya 8.5+ chunk tags: `FVCA`, `DVCA`, `DBLA`). Maya stores
time in *ticks* of `1/6000` second.

## class NCacheXML

```
NCacheXML(xml,
          fps=24,
          startFrame=1,
          endFrame=200,
          evalStep=1.0,
          channels=None,
          cacheFormat='mcc',
          cacheType='OneFilePerFrame')
```

`xml` is the path to the XML description file. `evalStep` is the evaluation
interval in frames (`0.5` for two samples per frame, `1.0` for one).

- `read()` — load an existing XML file into this instance.
- `write()` — serialize the current state to the XML path.
- `setXMLPath(xml)` / `getXMLPath()`
- `setFps(fps)` / `getFps()`
- `setStartFrame(frame)` / `getStartFrame()`
- `setEndFrame(frame)` / `getEndFrame()`
- `setSamplingRate(step)` / `getSamplingRate()` — sampling rate in ticks.
- `setChannels(channels)` / `getChannels()`
- `setFormat(fmt)` / `getFormat()` — `'mcc'` or `'mcx'`.
- `appendChannel(chName, chType='FloatVectorArray', chInter='positions')`
- `setChannelTypes(types)` / `getChannelTypes()` — each entry is one of
  `'DoubleArray'`, `'FloatVectorArray'`, `'DoubleVectorArray'`. For Geometry
  Cache all channels should share the same type.
- `setChannelInters(inters)` / `getChannelInters()`
- `getXMLString()` — current XML serialization as a string.

## class NCacheMC

```
NCacheMC(xml_path, frame=1, channels=None, pointsArray=None)
```

A single cache data file. The on-disk path is derived from `xml_path` and
`frame`; `pointsArray` is a list of numpy 2D arrays (one per channel).

- `read()` / `write()`
- `setFrame(frame)` / `getFrame()`
- `setXMLPath(xml_path)`
- `setChannels(channels)` / `getChannels()`
- `setPointArray(pArray)` / `getPointArray()`
- `getAmount()` — total point count across all channels.
- `getPath()` — current cache file path.
- `getChannelTypes()`
- `getEleAmounts()` — per-channel element count.

## class NPCacheXML

Subclass of `NCacheXML` specialized for nParticle caches. nParticle channels
carry per-attribute data of varying type and length, so the parent's
`ChannelInterpretation` field is repurposed as the attribute name. Channel
names are auto-generated from the nParticle node name and the attribute.
Channel types are passed as integer tags:

| code | type                |
| ---- | ------------------- |
| 0    | `DoubleArray`       |
| 1    | `FloatVectorArray`  |
| 2    | `DoubleVectorArray` |

```
NPCacheXML(xml_path,
           name='nParticleShape',
           attrs=['id', 'count', 'position'],
           chTypes=[0, 0, 1])
```

The `id` attribute is required.

- `setName(name)` / `getName()`
- `setAttrs(attrs)` — list of attribute names.
- `setChannelTypes(chTypes)` — list of integer tags as above.
- `appendAttr(attr, attrType)` — `attr` str, `attrType` int.

## class NPCacheMC

Subclass of `NCacheMC` with per-attribute accessors. Attribute values come
back as numpy arrays whose shape depends on the channel type: vector arrays
are `n x 3`, scalar arrays are 1D, and `count` is a single-element array.

```
NPCacheMC(xml_path)
```

- `getName()` / `getAttrs()`
- `getAttrValues(attr)` — numpy array for the named attribute.
- `getStartFrame()` / `getEndFrame()`

## HDAs

The `HDAs/` directory contains Houdini Digital Assets for exporting caches
from Houdini. See [HDAs/README.md](HDAs/README.md) for details on each HDA,
including parameter descriptions and how to match the `particle_name` setting
to your Maya scene.

## Houdini export

`houdini_export()` is the entry point invoked from the HDA's PythonModule,
which loads `nCache.py` at runtime via `importlib.util`. It reads the HDA
parameters (`start_frame`, `end_frame`,
`eval_rate`, `particle_name`, `xml`), inspects the point attributes on the
`WRITE_OUT` SOP, and writes one `.mc` per (frame, sub-frame) pair. The
Houdini attribute names are mapped to the conventional Maya nParticle
attributes:

| Houdini  | Maya nParticle | Channel type        |
| -------- | -------------- | ------------------- |
| `id`     | `id`           | `DoubleArray`       |
| `P`      | `position`     | `FloatVectorArray`  |
| `v`      | `velocity`     | `FloatVectorArray`  |
| `age`    | `age`          | `DoubleArray`       |
| `life`   | `lifespanPP`   | `DoubleArray`       |
| `pscale` | `radiusPP`     | `DoubleArray`       |
| `Cd`     | `rgbPP`        | `FloatVectorArray`  |
| `Alpha`  | `opacityPP`    | `DoubleArray`       |
| `rotation` | `rotationPP` | `FloatVectorArray`  |

`id` must exist on every frame; export aborts with a warning if it does not.
