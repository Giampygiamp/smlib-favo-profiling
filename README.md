# SMLib profiling study: honeycomb (favo) on a sphere

An independent, unofficial study of the boundary-representation kernel **SMLib**
(part of [NVIDIA-Omniverse/usd-brep](https://github.com/NVIDIA-Omniverse/usd-brep) 1.0.0,
Apache-2.0). It documents

1. how to build the SMLib kernel and its Python module on Linux without Packman/premake and without USD,
2. a real test case: a spherical shell with a honeycomb of 746 hexagonal pockets (we use up to 300),
3. where the time goes (callgrind profile) and why it slows down as pockets accumulate,
4. two small experimental patches that cut the Boolean time by about 45% with identical output on this test.

> **Status:** experimental, measured on one geometry family only (sphere with planar pockets).
> Not tested with the upstream C++ test suite. Not an NVIDIA product or contribution.
> NVIDIA does not accept external code contributions to the upstream repository, so the patches live here.

## Results

Same bench, same cells, kernel as shipped vs. kernel with both patches enabled
(`SMLIB_FAST_LOOP=1 SMLIB_FAST_PAIRS=1`). Cloud machine, 2 cores, Linux, g++ 13, `-O2 -g`.

| Test | Original kernel | Patched | Change |
|---|---|---|---|
| 150 pockets, Boolean time | 29.1 s | 15.5-16.4 s | about -45% |
| 300 pockets, Boolean time | 118.7 s | 65.8 s | -45% |
| Instructions, 120 pockets (callgrind) | 103.7 G | 54.8 G | -47% (FAST_LOOP alone: 67.1 G) |

Output was identical in every run: same final volume (2,485,581 for 150 pockets;
2,394,459 for 300), same face count (1329; 2713), same discarded cells.

## Where the time goes (original kernel, 120 pockets)

- About 83% in `SmMerge::ManifoldBoolean`, of which 78% in `SmTopologyIntersector::IntersectInsertRelate`.
- 49% in `SmFace::PointClassify` / `SmLoop::ContainsUVPoint`: to classify a point on a face the kernel walks
  **every loop** of that face and samples every curve (25.7 M B-spline evaluations). The sphere gets one loop
  per pocket already cut, so each query costs more as pockets accumulate.
- 42% in `SmFace::FaceIntersect` (719,626 calls): `IntersectTopology` tests **all face pairs** of the two solids,
  without discarding distant pairs by bounding box at that point.

## The two patches (`smlib_fast_experiment.patch`)

Both are inactive unless an environment variable is set, so the kernel behaves exactly as upstream without them.

- `SMLIB_FAST_LOOP=1` (`SmLoop.cpp`): in `ContainsUVPoint`, if the UV box of the loop's trim curves (conservative,
  from control polygons) lies strictly inside the surface's natural UV domain and the point is clearly outside that
  box, answer "outside" immediately. It only applies to "island" loops; loops touching the domain boundary
  (poles, seams) still use the full computation.
- `SMLIB_FAST_PAIRS=1` (`SmTopologyIntersector.cpp`): before testing two faces, skip the pair if their 3D bounding
  boxes (computed once per face, with a margin of 10 times the tolerance) are disjoint.

Apply to a clean checkout of usd-brep 1.0.0:

```
git clone https://github.com/NVIDIA-Omniverse/usd-brep
cd usd-brep && patch -p1 < ../smlib-favo-profiling/smlib_fast_experiment.patch
```

## Reproduce (Linux)

```
sudo apt install g++ libtbb-dev python3-dev
pip install pybind11 numpy scipy
git clone https://github.com/NVIDIA-Omniverse/usd-brep ~/usd-brep      # paths in the Makefiles start from $HOME/usd-brep
make -f Makefile.smlib -j2        # kernel (224 .cpp files) -> libSMLib.so
make -f Makefile.api_py -j2       # SM_API + Python module _omni_solid (USD part replaced by usd_stub.cpp)
export PYTHONPATH=$PWD LD_LIBRARY_PATH=$PWD
# run from this repository folder: the scripts read favo_cells.txt from the current directory
python favo_k.py 150
SMLIB_FAST_LOOP=1 SMLIB_FAST_PAIRS=1 python favo_k.py 150
```

The scripts build each hexagonal cell as an intersection of oriented half-space boxes, then subtract one cell at a
time from the shell (sphere R=111 mm minus sphere R=91 mm). The official route on Windows is `prebuild.bat` +
`repo.bat build` (not tried here).

## Known limits and open points

- Measurements come from a 2-core cloud machine and from this specific bench. Do not compare these times with
  other software or other procedures.
- About 10% of the cells (16 of 150, 21 of 300) are discarded because the result is not a valid solid
  (`is_manifold_solid` false); identical with and without the patches. Cause not yet understood
  (cell construction or the validity check).
- Memory grows faster than linearly (about 4 GB at 300 pockets). Cause not investigated.
- After the patches `ContainsUVPoint` still takes about 25% of the time (loops touching the UV domain boundary).
- The upstream C++ tests were not run; of 400 Python-module tests, 362 pass (the other 38 need the USD part,
  which this build omits), with and without the patches.
- TBB parallel paths (not enabled in the official build) were not tried.

## Author

Giampiero Partenzi (analysis, test bench, patches and measurements, carried out with the help of Claude, an AI assistant by Anthropic).
The honeycomb cell data in `favo_cells.txt` come from the author's own sphere-honeycomb project and are published with his permission.

## License

Apache License 2.0, see `LICENSE` and `NOTICE`. The patched files derive from NVIDIA's USD BRep (Apache-2.0).
