# HDAs

Houdini Digital Assets for Maya cache export.

---

## export_Maya_nParticles_cache.hda

Exports a Houdini point sequence as a Maya **nParticle cache**
(`.xml` descriptor + one `.mc` binary per frame).

### Parameters

| Parameter | Description |
|-----------|-------------|
| Start / End Frame | Frame range to export |
| Evaluation Rate | Samples per frame (`1` = one per frame, `0.5` = two per frame) |
| XML | Output path for the `.xml` descriptor file |
| **Particle Name** | Base name — see below |
| Cache | Click to run the export |
| Python Module Path | Path to `nCache.py` |

### Particle Name and Maya Node Naming

`particle_name` is the single setting that must agree between Houdini and Maya.

The HDA appends `Shape` to whatever you enter and uses the result as the
**prefix** for every channel in the cache:

```
channel names = <particle_name>Shape_id
                <particle_name>Shape_count
                <particle_name>Shape_position
                <particle_name>Shape_velocity
                ...
```

Maya's nCache system maps channels to an nParticle object by matching this
prefix to the **nParticle shape node name**.  If they don't match, Maya
silently ignores the cache.

| Particle Name | Channel prefix | Maya shape must be named |
|---------------|---------------|--------------------------|
| `nParticle`   | `nParticleShape_*` | `nParticleShape` |
| `particle`    | `particleShape_*`  | `particleShape`  |
| `dust`        | `dustShape_*`      | `dustShape`      |

**Workflow:**

1. In Maya's Outliner (Shapes enabled), note the exact name of your nParticle
   shape node.
2. Remove the `Shape` suffix — the remainder is your `particle_name`.
3. Set **Particle Name** to that value before exporting.

### Source Geometry Requirements

The HDA reads each frame's geometry via `geometryAtFrame()` — it does **not**
step through the global frame counter. This means a live DOP simulation
connected directly to the input will not cook correctly (the simulation
cannot accumulate state by jumping frames).

**Always bake your particle simulation to a geometry cache (e.g. a File Cache
SOP or bgeo sequence) before connecting it to this HDA.**

### Attaching in Maya

Use **FX > nCache > Attach Existing Cache** and select the `.xml` file.
Do **not** use File > Import — it will not create the nParticle cache connections.

---

## export_Maya_geoCache.hda

Exports a Houdini geometry sequence as a Maya **geometry cache**
(`.xml` + `.mc` files for deforming mesh playback).

### Parameters

| Parameter | Description |
|-----------|-------------|
| Start / End Frame | Frame range to export |
| Evaluation Rate | Samples per frame (`1` = one per frame, `0.5` = two per frame) |
| XML | Output path for the `.xml` descriptor file |
| Cache | Click to run the export |
| Python Module Path | Path to `nCache.py` |

### Point Group and Maya Node Naming

Each Houdini **point group** on the input geometry becomes one channel in the
cache. The group name must exactly match the Maya **shape node name** of the
mesh it should drive.

| Houdini point group | Maya shape node it drives |
|---------------------|---------------------------|
| `pSphereShape1`     | `pSphereShape1`           |
| `bodyMeshShape`     | `bodyMeshShape`           |

The vertex count and order in the point group must match the Maya mesh exactly.

### Source Geometry Requirements

This HDA uses `geometryAtFrame()` and does **not** step the global frame
counter. A live DOP simulation connected directly will produce incorrect
results. **Always bake your simulation to a geometry cache first.**

### Attaching in Maya

Select the target mesh(es), then use **Cache > Geometry Cache > Attach
Existing Cache** and select the `.xml` file.
Do **not** use File > Import — it will not create the cache connections.
