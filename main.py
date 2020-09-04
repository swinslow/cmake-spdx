# SPDX-License-Identifier: Apache-2.0

import sys

from cmakefileapijson import parseReply

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path-to-cmake-api-index.json>")
        sys.exit(1)

    replyIndexPath = sys.argv[1]
    cm = parseReply(replyIndexPath)
