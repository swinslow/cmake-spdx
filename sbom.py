# SPDX-License-Identifier: Apache-2.0

import hashlib
import os

from cmakefileapi import TargetType
from cmakefileapijson import parseReply
from spdx.builder import BuilderConfig, makeSPDX
from spdx.relationships import outputSPDXRelationships

def getCmakeRelationships(cm):
    """
    Extracts details from Cmake API about which built files derive from
    which sources. Looks at all targets within the first configuration
    in the CodeModel.

    Arguments:
        - cm: CodeModel
    Returns: list of tuples with relationships: [(filepath1, rln, filepath2), ...]
    """
    # get relative path: os.path.relpath(filename, cfg.scandir)
    rlns = []
    # walk through targets
    for cfgTarget in cm.configurations[0].configTargets:
        target = cfgTarget.target
        # FIXME currently only handles static / object libraries
        # for static / object libraries or executables, gather source files
        if target.type in [TargetType.EXECUTABLE, TargetType.STATIC_LIBRARY, TargetType.OBJECT_LIBRARY]:
            # FIXME currently only handles one artifact in list
            if len(target.artifacts) != 1:
                print(f"For target {target.name}, expected 1 artifact, got {len(target.artifacts)}; not generating relationships")
                continue
            artifactPath = target.artifacts[0]
            for src in target.sources:
                newRln = (os.path.join(".", artifactPath), "GENERATED_FROM", src.path)
                rlns.append(newRln)
            # also, if any dependencies of static libraries or executables created
            # artifacts, include STATIC_LINK relationships for those
            if target.type in [TargetType.EXECUTABLE, TargetType.STATIC_LIBRARY]:
                for dep in target.dependencies:
                    # now we need to find the target with this dep's ID
                    for depCfgTarget in cm.configurations[0].configTargets:
                        depTarget = depCfgTarget.target
                        if depTarget.id != dep.id:
                            continue
                        # now we've got the right one; check the dep types
                        # only link in library dependencies, not utility or executable
                        if depTarget.type in [TargetType.STATIC_LIBRARY, TargetType.OBJECT_LIBRARY]:
                            if len(depTarget.artifacts) != 1:
                                print(f"For dependency {depTarget.name}, expected 1 artifact, got {len(depTarget.artifacts)}; not generating linking relationship")
                                continue
                            depArtifactPath = depTarget.artifacts[0]
                            newDepRln = (os.path.join(".", artifactPath), "STATIC_LINK", os.path.join(".", depArtifactPath))
                            rlns.append(newDepRln)
                            break
    return rlns

def makeCmakeSpdx(replyIndexPath, srcRootDir, spdxOutputDir, spdxNamespacePrefix):
    # get CMake info from build
    cm = parseReply(replyIndexPath)

    # create SPDX file for sources
    srcSpdxPath = os.path.join(spdxOutputDir, "sources.spdx")
    srcCfg = BuilderConfig()
    srcCfg.documentName = "sources"
    srcCfg.documentNamespace = os.path.join(spdxNamespacePrefix, "sources")
    srcCfg.packageName = "sources"
    srcCfg.spdxID = "SPDXRef-sources"
    srcCfg.doSHA256 = True
    srcCfg.scandir = srcRootDir
    srcCfg.excludeDirs.append(cm.paths_build)
    srcPkg = makeSPDX(srcCfg, srcSpdxPath)
    if srcPkg:
        print(f"Saved sources SPDX to {srcSpdxPath}")
    else:
        print(f"Couldn't generate sources SPDX file")

    # get hash of sources SPDX file, to use for build doc's extRef
    hSHA256 = hashlib.sha256()
    with open(srcSpdxPath, 'rb') as f:
        buf = f.read()
        hSHA256.update(buf)
    srcSHA256 = hSHA256.hexdigest()

    # get auto-generated relationships between filenames
    fileRlns = getCmakeRelationships(cm)

    # create SPDX file for build
    buildSpdxPath = os.path.join(spdxOutputDir, "build.spdx")
    buildCfg = BuilderConfig()
    buildCfg.documentName = "build"
    buildCfg.documentNamespace = os.path.join(spdxNamespacePrefix, "build")
    buildCfg.packageName = "build"
    buildCfg.spdxID = "SPDXRef-build"
    buildCfg.doSHA256 = True
    buildCfg.scandir = cm.paths_build

    # add external document ref to sources SPDX file
    buildCfg.extRefs = [("DocumentRef-sources", srcCfg.documentNamespace, "SHA256", srcSHA256)]

    # exclude CMake file-based API responses -- presume only used for this
    # SPDX generation scan, not for actual build artifact
    buildExcludeDir = os.path.join(cm.paths_build, ".cmake", "api")
    buildCfg.excludeDirs.append(buildExcludeDir)

    buildPkg = makeSPDX(buildCfg, buildSpdxPath)
    if buildPkg:
        print(f"Saved build SPDX to {buildSpdxPath}")
    else:
        print(f"Couldn't generate build SPDX file")

    # and print relationships to build file also
    retval = outputSPDXRelationships(srcRootDir, srcPkg, buildPkg, fileRlns, buildSpdxPath)
    if retval:
        print(f"Added relationships to {buildSpdxPath}")
    else:
        print(f"Couldn't add relationships to build SPDX file")
