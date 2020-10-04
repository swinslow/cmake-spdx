# SPDX-License-Identifier: Apache-2.0

import os

def resolveRelationshipID(srcRootDir, srcPkg, buildPkg, filepath):
    """
    Determines the corresponding SPDX ID for filepath, depending on whether
    it is a source file or build file.

    Arguments:
        - srcRootDir: root directory of sources being scanned
        - srcPkg: source SPDX Package section data
        - buildPkg: build SPDX Package section data
        - filepath: path to file being resolved; might be absolute or relative

    Returns: tuple (is_build, identifier) where:
             is_build is True if filepath is for a build file, False if source file
             identifier is the resolved ID or None if not resolvable
    """
    # figure out relative path we're searching for
    # FIXME this is probably not the right way to do this
    is_build = filepath.startswith("./") or filepath.startswith(".\\")

    if is_build:
        pkg = buildPkg
        searchPath = filepath
    else:
        pkg = srcPkg
        # make sure filepath is actually within the sources root dir
        checkPath = os.path.relpath(filepath, srcRootDir)
        # FIXME this is also probably not the right way to do this
        if checkPath.startswith("../") or checkPath.startswith("..\\"):
            # points to somewhere outside our sources root dir;
            # we won't be able to create this relationship
            print(f"{filepath} is not in sources root dir {srcRootDir}, can't create relationship")
            return (is_build, None)
        searchPath = os.path.join(".", checkPath)

    # search through files for the one with this filename
    for f in pkg.files:
        if f.name == searchPath:
            return (is_build, f.spdxID)

    print(f"{filepath} not found in package, can't create relationship")
    return (is_build, None)

def outputSPDXRelationships(srcRootDir, srcPkg, buildPkg, rlns, spdxPath):
    """
    Create and append SPDX relationships to the end of the previously-created
    SPDX build document.

    Arguments:
        - srcRootDir: root directory of sources being scanned
        - srcPkg: source SPDX Package section data
        - buildPkg: build SPDX Package section data
        - rlns: Cmake relationship data from call to getCmakeRelationships()
        - spdxPath: path to previously-started SPDX build document
    Returns: True on success, False on error.
    """
    try:
        with open(spdxPath, "a") as f:
            for rln in rlns:
                (is_buildA, rlnIDA) = resolveRelationshipID(srcRootDir, srcPkg, buildPkg, rln[0])
                (is_buildB, rlnIDB) = resolveRelationshipID(srcRootDir, srcPkg, buildPkg, rln[2])
                if not rlnIDA or not rlnIDB:
                    continue

                # add DocumentRef- prefix for sources files
                if not is_buildA:
                    rlnIDA = "DocumentRef-sources:" + rlnIDA
                if not is_buildB:
                    rlnIDB = "DocumentRef-sources:" + rlnIDB

                f.write(f"Relationship: {rlnIDA} {rln[1]} {rlnIDB}\n")
            return True

    except OSError as e:
        print(f"Error: Unable to append to {spdxPath}: {str(e)}")
        return False
