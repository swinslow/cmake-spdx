# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
import hashlib
import os
import re

class BuilderConfig:
    def __init__(self):
        super(BuilderConfig, self).__init__()

        #####
        ##### Document info
        #####

        # name of document
        self.documentName = ""

        # namespace for this document
        self.documentNamespace = ""

        #####
        ##### Package / scan info
        #####

        # FIXME consider changing this to an array of multiple package configs
        # FIXME so that one document can contain multiple packages

        # name of package
        self.packageName = ""

        # SPDX ID for package, must begin with "SPDXRef-"
        self.spdxID = ""

        # download location for package, defaults to "NOASSERTION"
        self.packageDownloadLocation = "NOASSERTION"

        # should conclude package license based on detected licenses,
        # AND'd together?
        self.shouldConcludeLicense = True

        # declared license, defaults to "NOASSERTION"
        self.declaredLicense = "NOASSERTION"

        # copyright text, defaults to "NOASSERTION"
        self.copyrightText = "NOASSERTION"

        # should include SHA256 hashes? (will also include SHA1 regardless)
        self.doSHA256 = False

        # should include MD5 hashes? (will also include MD5 regardless)
        self.doMD5 = False

        # root directory to be scanned
        self.scandir = ""

        # directories whose files should not be included
        self.excludeDirs = [".git/"]

        # directories whose files should be included, but not scanned
        # FIXME not yet enabled
        self.skipScanDirs = []

        # number of lines to scan for SPDX-License-Identifier (0 = all)
        # defaults to 20
        self.numLinesScanned = 20

class BuilderPackage:
    def __init__(self):
        super(BuilderPackage, self).__init__()

        self.name = ""
        self.spdxID = ""
        self.downloadLocation = ""
        # FIXME not yet calculated
        self.verificationCode = ""
        self.licenseConcluded = ""
        self.licenseInfoFromFiles = []
        self.licenseDeclared = ""
        self.copyrightText = ""
        self.files = []

    def initFromConfig(self, cfg):
        self.name = cfg.packageName
        self.spdxID = cfg.spdxID
        self.downloadLocation = cfg.packageDownloadLocation
        self.verificationCode = ""
        self.licenseConcluded = "NOASSERTION"
        self.licenseInfoFromFiles = []
        self.licenseDeclared = cfg.declaredLicense
        self.copyrightText = cfg.copyrightText

class BuilderFile:
    def __init__(self):
        super(BuilderFile, self).__init__()

        self.name = ""
        self.spdxID = ""
        # FIXME not yet implementing FileType
        self.type = ""
        self.sha1 = ""
        self.sha256 = ""
        self.md5 = ""
        self.licenseConcluded = "NOASSERTION"
        self.licenseInfoInFile = []
        self.copyrightText = "NOASSERTION"

def shouldExcludeFile(filename, excludes):
    """
    Determines whether a file is in an excluded directory.

    Arguments:
        - filename: filename being tested
        - excludes: array of excluded directory names
    Returns: True if should exclude, False if not.
    """
    for exc in excludes:
        if exc in filename:
            return True
    return False

def getAllPaths(topDir, excludes):
    """
    Gathers a list of all paths for all files within topDir or its children.

    Arguments:
        - topDir: root directory of files being collected
        - excludes: array of excluded directory names
    Returns: array of paths
    """
    paths = []
    # ignoring second item in tuple, which lists immediate subdirectories
    for (currentDir, _, filenames) in os.walk(topDir):
        for filename in filenames:
            p = os.path.join(currentDir, filename)
            if not shouldExcludeFile(p, excludes):
                paths.append(p)
    return sorted(paths)

def parseLineForExpression(line):
    """Return parsed SPDX expression if tag found in line, or None otherwise."""
    p = line.partition("SPDX-License-Identifier:")
    if p[2] == "":
        return None
    # strip away trailing comment marks and whitespace, if any
    expression = p[2].strip()
    expression = expression.rstrip("/*")
    expression = expression.strip()
    return expression

def getExpressionData(filePath, numLines):
    """
    Scans the specified file for the first SPDX-License-Identifier:
    tag in the file.

    Arguments:
        - filePath: path to file to scan.
        - numLines: number of lines to scan for an expression before
                    giving up. If 0, will scan the entire file.
    Returns: parsed expression if found; None if not found.
    """
    with open(filePath, "r") as f:
        try:
            lineno = 0
            for line in f:
                lineno += 1
                if numLines > 0 and lineno > numLines:
                    break
                expression = parseLineForExpression(line)
                if expression is not None:
                    return expression
        except UnicodeDecodeError:
            # invalid UTF-8 content
            return None

    # if we get here, we didn't find an expression
    return None

def splitExpression(expression):
    """
    Parse a license expression into its constituent identifiers.

    Arguments:
        - expression: SPDX license expression
    Returns: array of split identifiers
    """
    # remove parens and plus sign
    e2 = re.sub(r'\(|\)|\+', "", expression, flags=re.IGNORECASE)

    # remove word operators, ignoring case, leaving a blank space
    e3 = re.sub(r' AND | OR | WITH ', " ", e2, flags=re.IGNORECASE)

    # and split on space
    e4 = e3.split(" ")

    return sorted(e4)

def getHashes(filePath):
    """
    Scan for and return hashes.

    Arguments:
        - filePath: path to file to scan.
    Returns: tuple of (SHA1, SHA256, MD5) hashes for filePath.
    """
    hSHA1 = hashlib.sha1()
    hSHA256 = hashlib.sha256()
    hMD5 = hashlib.md5()

    with open(filePath, 'rb') as f:
        buf = f.read()
        hSHA1.update(buf)
        hSHA256.update(buf)
        hMD5.update(buf)

    return (hSHA1.hexdigest(), hSHA256.hexdigest(), hMD5.hexdigest())

def makeFileData(filePath, cfg, fileno):
    """
    Scan for expression, get hashes, and fill in data.

    Arguments:
        - filePath: path to file to scan.
        - cfg: BuilderConfig for this scan.
        - fileno: unique filenumber (used for SPDX ID)
    Returns: BuilderFile
    """
    bf = BuilderFile()
    bf.name = filePath
    bf.spdxID = f"SPDXRef-File{fileno}"

    (sha1, sha256, md5) = getHashes(filePath)
    bf.sha1 = sha1
    if cfg.doSHA256:
        bf.sha256 = sha256
    if cfg.doMD5:
        bf.md5 = md5

    expression = getExpressionData(filePath, cfg.numLinesScanned)
    if expression != None:
        bf.licenseConcluded = expression
        bf.licenseInfoInFile = splitExpression(expression)

    return bf

def makeAllFileData(filePaths, cfg):
    """
    Scan all files for expressions and hashes, and fill in data.

    Arguments:
        - filePaths: sorted array of paths to files to scan.
        - cfg: BuilderConfig for this scan.
    Returns: array of BuilderFiles
    """
    bfs = []
    fileno = 1
    for filePath in filePaths:
        bf = makeFileData(filePath, cfg, fileno)
        fileno += 1
        bfs.append(bf)

    return bfs

def getPackageLicenses(bfs):
    """
    Extract lists of all concluded and infoInFile licenses seen.

    Arguments:
        - bfs: array of BuilderFiles
    Returns: tuple(sorted list of concluded license exprs,
                   sorted list of infoInFile ID's)
    """
    licsConcluded = set()
    licsFromFiles = set()
    for bf in bfs:
        licsConcluded.add(bf.licenseConcluded)
        for licInfo in bf.licenseInfoInFile:
            licsFromFiles.add(licInfo)
    return (sorted(list(licsConcluded)), sorted(list(licsFromFiles)))

def normalizeExpression(licsConcluded):
    """
    Combine array of license expressions into one AND'd expression,
    adding parens where needed.

    Arguments:
        - licsConcluded: array of license expressions
    Returns: string with single AND'd expression.
    """
    # return appropriate for simple cases
    if len(licsConcluded) == 0:
        return "NOASSERTION"
    if len(licsConcluded) == 1:
        return licsConcluded[0]

    # more than one, so we'll need to combine them
    # iff an expression has spaces, it needs parens
    revised = []
    for lic in licsConcluded:
        if lic == "NONE" or lic == "NOASSERTION":
            continue
        if " " in lic:
            revised.append(f"({lic})")
        else:
            revised.append(lic)
    return " AND ".join(revised)

def makePackageData(cfg):
    """
    Create package and call sub-functions to scan and create file data.

    Arguments:
        - cfg: BuilderConfig for this scan.
    Returns: BuilderPackage
    """
    pkg = BuilderPackage()
    pkg.initFromConfig(cfg)

    filePaths = getAllPaths(cfg.scandir, cfg.excludeDirs)
    bfs = makeAllFileData(filePaths, cfg)
    (licsConcluded, licsFromFiles) = getPackageLicenses(bfs)

    if cfg.shouldConcludeLicense:
        pkg.licenseConcluded = normalizeExpression(licsConcluded)
    pkg.licenseInfoFromFiles = licsFromFiles
    pkg.files = bfs

    return pkg

def outputSPDX(pkg, cfg, spdxPath):
    """
    Write SPDX doc, package and files content to disk.

    Arguments:
        - pkg: BuilderPackage from makePackageData
        - cfg: BuilderConfig
        - spdxPath: path to write SPDX content
    Returns: True on success, False on error.
    """
    try:
        with open(spdxPath, 'w') as f:
            # write document creation info section
            f.write(f"""SPDXVersion: SPDX-2.2
DataLicense: CC0-1.0
SPDXID: SPDXRef-DOCUMENT
DocumentName: {cfg.documentName}
DocumentNamespace: {cfg.documentNamespace}
Creator: Tool: cmake-spdx
Created: {datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}

""")

            # write package section
            f.write(f"""PackageName: {pkg.name}
SPDXID: {pkg.spdxID}
PackageDownloadLocation: {pkg.downloadLocation}
FilesAnalyzed: true
PackageVerificationCode: {pkg.verificationCode}
PackageLicenseConcluded: {pkg.licenseConcluded}
""")
            for licFromFiles in pkg.licenseInfoFromFiles:
                f.write(f"PackageLicenseInfoFromFiles: {licFromFiles}\n")
            f.write(f"""PackageLicenseDeclared: {pkg.licenseDeclared}
PackageCopyrightText: NOASSERTION

Relationship: SPDXRef-DOCUMENT DESCRIBES {pkg.spdxID}

""")

            # write file sections
            for bf in pkg.files:
                f.write(f"""FileName: {bf.name}
SPDXID: {bf.spdxID}
FileChecksum: SHA1: {bf.sha1}
""")
                if bf.sha256 != "":
                    f.write(f"FileChecksum: SHA256: {bf.sha256}\n")
                if bf.md5 != "":
                    f.write(f"FileChecksum: MD5: {bf.md5}\n")
                f.write(f"LicenseConcluded: {bf.licenseConcluded}\n")
                if len(bf.licenseInfoInFile) == 0:
                    f.write(f"LicenseInfoInFile: NONE\n")
                else:
                    for licInfoInFile in bf.licenseInfoInFile:
                        f.write(f"LicenseInfoInFile: {licInfoInFile}\n")
                f.write(f"FileCopyrightText: {bf.copyrightText}\n\n")

            # we're done for now; will do other relationships later
            return True

    except OSError as e:
        print(f"Unable to write to {spdxPath}: {str(e)}")
        return False

def makeSPDX(cfg, spdxPath):
    """
    Scan, create and write SPDX details to disk.

    Arguments:
        - cfg: BuilderConfig
        - spdxPath: path to write SPDX content
    Returns: True on success, False on error.
    """
    pkg = makePackageData(cfg)
    return outputSPDX(pkg, cfg, spdxPath)