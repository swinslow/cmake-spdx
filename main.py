# SPDX-License-Identifier: Apache-2.0

import sys

from sbom import makeCmakeSpdx

if __name__ == "__main__":
    replyIndexPath = "/home/steve/programming/zephyr/zephyrproject/zephyr/build/.cmake/api/v1/reply/index-2020-12-30T22-00-13-0162.json"
    srcRootDirs = {
        "blinky": "/home/steve/programming/zephyr/zephyrproject/zephyr/samples/basic/blinky",
        "zephyr": "/home/steve/programming/zephyr/zephyrproject",
    }
    spdxOutputDir = "/home/steve/programming/spdx/cmake-spdx/scratch"
    spdxNamespacePrefix = "https://swinslow.net/cmake-spdx"
    makeCmakeSpdx(replyIndexPath, srcRootDirs, spdxOutputDir, spdxNamespacePrefix)

#if __name__ == "__main__":
#    if len(sys.argv) < 5:
#        print(f"Usage: {sys.argv[0]} <path-to-cmake-api-index.json> <path-to-top-level-sources> <spdx-output-dir> <spdx-namespace-prefix>")
#        sys.exit(1)
#
#    replyIndexPath = sys.argv[1]
#    srcRootDir = sys.argv[2]
#    spdxOutputDir = sys.argv[3]
#    spdxNamespacePrefix = sys.argv[4]
#    makeCmakeSpdx(replyIndexPath, srcRootDir, spdxOutputDir, spdxNamespacePrefix)
