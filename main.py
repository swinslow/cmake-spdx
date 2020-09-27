# SPDX-License-Identifier: Apache-2.0

import os
import sys

from cmakefileapijson import parseReply
from spdx.builder import BuilderConfig, makeSPDX

def makeCmakeSpdx(replyIndexPath, srcRootDir, spdxOutputDir, spdxNamespacePrefix):
    # get CMake info from build
    replyIndexPath = sys.argv[1]
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

    # create SPDX file for build
    buildSpdxPath = os.path.join(spdxOutputDir, "build.spdx")
    buildCfg = BuilderConfig()
    buildCfg.documentName = "build"
    buildCfg.documentNamespace = os.path.join(spdxNamespacePrefix, "build")
    buildCfg.packageName = "build"
    buildCfg.spdxID = "SPDXRef-build"
    buildCfg.doSHA256 = True
    buildCfg.scandir = cm.paths_build
    # exclude CMake file-based API responses -- presume only used for this
    # SPDX generation scan, not for actual build artifact
    buildExcludeDir = os.path.join(cm.paths_build, ".cmake", "api")
    print(f"buildExcludeDir = {buildExcludeDir}")
    buildCfg.excludeDirs.append(buildExcludeDir)
    buildPkg = makeSPDX(buildCfg, buildSpdxPath)
    if buildPkg:
        print(f"Saved build SPDX to {buildSpdxPath}")
    else:
        print(f"Couldn't generate build SPDX file")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(f"Usage: {sys.argv[0]} <path-to-cmake-api-index.json> <path-to-top-level-sources> <spdx-output-dir> <spdx-namespace-prefix>")
        sys.exit(1)

    replyIndexPath = sys.argv[1]
    srcRootDir = sys.argv[2]
    spdxOutputDir = sys.argv[3]
    spdxNamespacePrefix = sys.argv[4]
    makeCmakeSpdx(replyIndexPath, srcRootDir, spdxOutputDir, spdxNamespacePrefix)
