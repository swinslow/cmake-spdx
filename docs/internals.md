# How cmake-spdx works

Here's a quick overview of the files comprising cmake-spdx:
  * [`cmakefileapi.py`](/cmakefileapi.py): Python classes for an in-memory representation of the [CMake file-based API codemodel objects](https://cmake.org/cmake/help/latest/manual/cmake-file-api.7.html#object-kind-codemodel)
  * [`cmakefileapijson.py`](/cmakefileapijson.py): functionality to take a CMake API response's set of JSON files and parse it into the classes in `cmakefileapi.py`
  * [`makedot.py`](/makedot.py): _not currently used_; experiment used to create a Graphiz DOT file used to visualize the target dependency relationships in the CMake response
  * [`sbom.py`](/sbom.py): entry point (makeCmakeSpdx) to create the source and build SPDX documents
  * [`spdx/builder.py`](/spdx/builder.py): scans a given directory and creates a corresponding SPDX document
  * [`spdx/relationships.py`](/spdx/relationships.py): creates the [SPDX Relationships](https://spdx.github.io/spdx-spec/7-relationships-between-SPDX-elements/) between the built files and the corresponding source files
  * [`main.py`](/main.py): main entry point, calls makeCmakeSpdx from sbom.py

Below are a few comments on a couple of the perhaps-less-obvious parts of this.

## Building an SPDX document

cmake-spdx creates two SPDX documents: one for [source files](/example/sources.spdx) and one for [built / binary files](/example/build.spdx).
`spdx/builder.py` contains the functionality for this.
At a high level, it does the following:

* is configured by the caller with a `BuilderConfig` object, with various settings for how the scan should run and what data should be included in the generated document
* creates one [SPDX Package section](https://spdx.github.io/spdx-spec/3-package-information/) representing the contents of the root directory being scanned (BuilderConfig.scandir)
* for each file contained within that directory (or its subdirectories):
  * scans the file for an [SPDX short-form identifier](https://spdx.dev/ids) (e.g., `SPDX-License-Identifier: Apache-2.0`)
  * if found, concludes that as being the license for the file
  * whether or not found, generates SHA1 and SHA256 hashes for the file
    * note that SHA1 is mandatory for SPDX 2.2: see [here](https://spdx.github.io/spdx-spec/4-file-information/#44-file-checksum)
  * creates a unique SPDX identifier for the file (see below for more details)
  * uses the collected data to create one [SPDX File section](https://spdx.github.io/spdx-spec/4-file-information/) for the file
* after scanning all of the files:
  * calculates an [SPDX Package Verification Code](https://spdx.github.io/spdx-spec/3-package-information/#39-package-verification-code) based on the files' SHA1 hashes
  * creates a concluded license for the package as a whole, by concatenating each of the detected licenses together with `AND` operators
  * also filling in some of the other mandatory Package section fields

## Source and Build SPDX documents

As mentioned above, cmake-spdx first builds and saves two SPDX documents, one for sources and another for the built files.
After these are built and saved to disk, it then scans through the dependency information in the CMake file API responses and uses that to create [SPDX Relationships](https://spdx.github.io/spdx-spec/7-relationships-between-SPDX-elements/).

There are two types of Relationships that cmake-spdx currently handles:
* `GENERATED_FROM`: this is used to indicate when a .c file is compiled into a binary.
* `STATIC_LINK`: this is used to indicate when a binary file from a preceding step (such as libkernel.a) is a dependency for another binary target (such as zephyr.elf).

The function `getCmakeRelationships` in `sbom.py` walks through the CMake file API responses to collect the relevant data for these relationships.
The functions in `spdx/relationships.py` then do the work of resolving the file paths into their corresponding SPDX identifiers, and then creating and writing the actual relationship data in SPDX format.

The Relationships are appended to the end of the build SPDX document.
Where a part of a Relationship refers to a build file (in other words, one which is defined in the build SPDX document), the identifier alone is used.
Where it refers to a sources file (which is defined in the sources SPDX document), a `DocumentRef-sources:` prefix appears before the identifier in the Relationship.
This is linked to the sources SPDX file by means of the `ExternalDocumentRef` tag at the top of the build SPDX file, which defines the reference to `DocumentRef-sources`.

The CMake file API responses in some contexts report file paths using relative locations, and sometimes using absolute locations.
Because of this, the absolute locations have to be rewritten into relative locations in order to be matched to the relative file paths used in the SPDX documents.

## Generating unique SPDX identifiers

A core concept of SPDX documents is that every SPDX element -- each Package or File (or other SPDX elements not used here) -- has a unique identifier.
An SPDX identifier always starts with `SPDXRef-` and is followed by a combination of letters, numbers, `-` and `.` which must be unique from any other SPDX identifier in the same document.

In an earlier version of the cmake-spdx proof of concept, it simply assigned every File a unique identifier that was a numeric iterator: `SPDXRef-File1`, `SPDXRef-File2`, etc.

This is a simple approach which is easy to implement.
The problem with it is that it makes the Relationships hard to understand.
`Relationship: SPDXRef-File-124 GENERATED_FROM DocumentRef-sources:SPDXRef-File-749` is not going to be semantically meaningful to a human without going and manually looking up the corresponding file paths.

To make it more user-friendly, the current version instead implements a process where the identifier incorporates the filename itself, with conversions for invalid characters.
So rather than the integer-based version shown above, it will instead generate more intuitive identifiers which cause relationships to look like the following: `Relationship: SPDXRef-File-libzephyr.a GENERATED_FROM DocumentRef-sources:SPDXRef-File-clock-stm32-ll-common.c`

One consideration in this is that the same filename can of course appear in multiple different directories. cmake-spdx handles this by keeping track of which identifiers it has seen, and for each duplicate it will add `-2`, `-3`, etc. as a suffix.

A further (likely rare) corner case resulting from this approach could occur with files whose actual filename ends with a hyphen and an integer, e.g. something like the following:
* `/src/base` => `SPDXRef-base`
* `/test/base` => `SPDXRef-base-2`
* `/test/base-2` => `SPDXRef-base-2`   `# INVALID, duplicate`

To avoid this, if an actual filename ends with a hyphen and an integer, then cmake-spdx assigns a numerical suffix even for the first instance of the file.
So in the above example it would actually be something more like:
* `/test/base-2` => `SPDXRef-base-2-1`

I haven't yet thought in further detail about whether this catches _all_ possible edge cases to ensure IDs are always unique, but I expect this should be an extremely rare edge case in any event.
