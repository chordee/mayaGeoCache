# HDAs

Houdini Digital Assets for Maya cache export.

---

## export_Maya_nParticles_cache.hda

Exports a Houdini point sequence as a Maya **nParticle cache**
(`.xml` descriptor + one `.mc` binary per frame).

> **nParticles only.**  This HDA targets Maya's **nParticles** system
> (introduced in Maya 2009, part of the Nucleus solver).  It is **not**
> compatible with Maya's legacy **particle** object (`nParticle` vs
> `particle` in the Create menu).  If your scene uses the old particle
> system, the cache channels will not connect.

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
| **Name Attribute** | Prim string attribute whose values become channel names (default: `name`) |
| Cache | Click to run the export |
| Python Module Path | Path to `nCache.py` |

### The `name` Attribute and Maya Shape Node Naming

Each unique value of the prim string attribute (default: `name`) becomes one
**channel** in the cache.  Maya maps each channel back to a mesh by matching
the channel name against the mesh's **shape node name**.

> **Shape node, not transform node.**  Maya users typically work with
> transform nodes in the Outliner and Viewport.  The shape node lives one
> level below the transform.  In the Outliner, enable **Show > Shapes** to
> see it.  Shape node names usually end in `Shape` (e.g. `pSphereShape1`
> for a transform named `pSphere1`).

Set the `name` primitive attribute on your geometry so that every primitive
belonging to a given mesh carries the corresponding shape node name.  Primitives
with an empty `name` value are skipped.

| Houdini prim `name` value | Maya shape node it drives |
|---------------------------|---------------------------|
| `pSphereShape1`           | `pSphereShape1`           |
| `bodyMeshShape`           | `bodyMeshShape`           |

#### Analogy: Houdini Alembic export

When Houdini exports an Alembic file it uses the `path` primitive attribute to
build the object hierarchy — each `/`-separated component becomes one level of
the hierarchy.  The `name` attribute here works the same way at the leaf level:
whatever string you assign to `name` on a primitive is exactly what Maya sees
as the channel name and matches against its shape nodes.

### Topology and Point Order

Maya geo cache has no concept of stable IDs.  It drives mesh deformation by
**replacing vertex positions in order** — vertex 0 in the cache overwrites
vertex 0 in the Maya mesh, vertex 1 overwrites vertex 1, and so on.

This means:
- The point count for each `name` value must be **identical** to the vertex
  count of the corresponding Maya mesh and must not change between frames.
- The **point order** must remain constant across all exported frames.
  If your simulation or procedural network reorders or rebuilds topology
  between frames, the cache will deform the mesh incorrectly.

Always verify point count and order are stable before exporting.

### Source Geometry Requirements

This HDA uses `geometryAtFrame()` and does **not** step the global frame
counter. A live DOP simulation connected directly will produce incorrect
results. **Always bake your simulation to a geometry cache first.**

### Attaching in Maya

You can select **multiple mesh objects** at once before attaching.  Maya reads
the `.xml`, finds every channel whose name matches a selected shape node, and
wires up each connection automatically — shapes with no matching channel are
left untouched.

Use **Cache > Geometry Cache > Attach Existing Cache** and select the `.xml` file.
Do **not** use File > Import — it will not create the cache connections.
