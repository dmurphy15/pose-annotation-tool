# pose-annotation-tool
Tool for annotating image sequences to build datasets for pose-estimation

## Use:
### Modes:
#### Single View Project:
Annotate images from a single view.

#### Multi View Project:
Annotate images from multiple views. 
Will need to supply projection matrices corresponding to each view to allow them to enforce that annotations are consistent across views.
The convention for the projection matrices is that they will treat the top-left corner of the image as coordinate (0,0) and the bottom-right corner as (1,1).

#### Depth View Project:
Not implemented

### Coordinate Systems:
2D annotations are written as (u,v) coordinates, where the u-axis goes left-to-right and the v-axis goes top-to-bottom. Each axis ranges from 0 to 1, so that the top-left corner of each image is (0,0) and the bottom-right corner is (1,1).
Similarly, projection matrices must be set up so that they map 3D coordinates to this same 2D space (between (0,0) and (1,1)).

### Shortcuts:
V: change View
F: change Frame Forward
B: change frame Back
J: change Joint
left-click: add annotation
right-click: delete annotation
