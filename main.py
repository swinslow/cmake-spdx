# SPDX-License-Identifier: Apache-2.0

import sys

from sbom import makeSpdxFromCmakeReply

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <path-to-cmake-api-index.json> <spdx-output-dir> <spdx-namespace-prefix>")
        sys.exit(1)

    replyIndexPath = sys.argv[1]
    spdxOutputDir = sys.argv[2]
    spdxNamespacePrefix = sys.argv[3]
    makeSpdxFromCmakeReply(replyIndexPath, spdxOutputDir, spdxNamespacePrefix)
