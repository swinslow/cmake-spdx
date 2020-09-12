# SPDX-License-Identifier: Apache-2.0

from cmakefileapi import TargetType

# Create a Graphviz DOT file corresponding to the relationships
# among targets in a CMake Config.
# takes: Config, DOT output filename
# returns: True on success, False on error
def makeDot(cfg, outfile):
    try:
        with open(outfile, "w") as f:
            f.write("digraph D {\n")

            # create node for each target
            nodeNum = 0
            nodeMap = {}
            for cfgTgt in cfg.configTargets:
                f.write(f"node{nodeNum} [label=\"{cfgTgt.name}\" shape={getShapeType(cfgTgt.target.type)}]\n")
                nodeMap[cfgTgt.target.id] = nodeNum
                nodeNum += 1

            # second pass, create edge for each dependency
            toNodeNum = 0
            for cfgTgt in cfg.configTargets:
                for dep in cfgTgt.target.dependencies:
                    fromNodeNum = nodeMap[dep.id]
                    f.write(f"node{fromNodeNum} -> node{toNodeNum}\n")
                toNodeNum += 1

            f.write("}\n")

    except OSError as e:
        print(f"Error writing to {outfile}: {str(e)}")
        return False

def getShapeType(targetType):
    if targetType == TargetType.EXECUTABLE:
        return "hexagon"
    elif targetType == TargetType.STATIC_LIBRARY:
        return "box"
    elif targetType == TargetType.SHARED_LIBRARY:
        return "octagon"
    elif targetType == TargetType.MODULE_LIBRARY:
        return "house"
    elif targetType == TargetType.OBJECT_LIBRARY:
        return "parallelogram"
    elif targetType == TargetType.UTILITY:
        return "oval"
    else:
        return "diamond"
