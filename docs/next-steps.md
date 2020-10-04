# What's not working / areas for improvement

## Assumes all sources are within the same root directory

cmake-spdx currently requires the user to pass in a "sources root directory" which contains all of the sources for the build: e.g. the application's sources, the main Zephyr sources and also the modules and other directories that are included in the build.
It then treats all of the sources together as a single SPDX [Package](https://spdx.github.io/spdx-spec/3-package-information/).

This makes an assumption that the main application is contained within the same set of directories as the Zephyr sources, which is correct for the blinky example used in the proof-of-concept run, but likely incorrect for other applications.

Even for the blinky example, doing it this way means that some of the relative paths are not correct when parsing relationships.
The current relationship matcher assumes incorrectly that all relative paths are relative to the declared "sources root directory", but this is incorrect: CMake reports the main application's source files as relative to the main application's sources directory, as `src/main.c` rather than `examples/basic/blinky/src/main.c`.
This means that it can't be traced back to the correct file when creating relationships, resulting in an error that gets printed during the run.

There is likely a better way to structure the sources SPDX document, where rather than a single Package being created, there are instead multiple Packages corresponding to the different directories or projects / targets that the CMake [codemodel file](/example/api-example-reply/api/v1/reply/codemodel-v2-018480969ba919525f17.json) reports.

However, I've reached the limits of my understanding of Zephyr, or west, or CMake for that matter, to be able to easily reason about what structure would be best here.
I've filed https://github.com/swinslow/cmake-spdx/issues/4 as a starting point for further discussion about how to improve this.

## Concluding licenses for binary files

Other than the issues described in further detail below, cmake-spdx currently does a good job of concluding the licenses for source files.
(Note, however, that it will only detect licenses via `SPDX-License-Identifier:` tags; it won't detect other license-relevant text that might be used in the repos.)

Since we know the licenses for source files, and we know which source files are compiled and linked into which binary files, cmake-spdx could take the next step of concluding licenses for the binary files as well.
Basically, the simple approach here would be to assume that all licenses in the relvant sources files will apply to the binary they are compiled into, and to `AND` them together into a single `LicenseConcluded` expression in the build SPDX document.

I've filed https://github.com/swinslow/cmake-spdx/issues/3 as a starting point to tackle this.

## Capturing missing relationships

The approach cmake-spdx uses to analyze the `codemodel` and `target` outputs from the CMake file API responses seems to work reasonably well, for determining e.g. which C files are compiled into which .a and .elf files.
However, it doesn't appear to provide an easy way to determine automatically which source files are compiled into other build artifacts (e.g. `zephyr.hex`, `zephyr.map`, etc.)

Someone with better knowledge of the Zephyr build process might be able to look at the various target outputs from the CMake API, and determine whether there's more relevant data that could be automatically extracted to create a better set of relationships.

## Invalid SPDX document due to invalid identifiers

When the source root directory to be scanned is just the main Zephyr sources (e.g., `zephyrproject/zephyr/`), all of the detected license identifiers are valid identifiers on the SPDX license list.
This means that the generated SPDX document is valid.
However, it is not complete, because it doesn't include e.g. files from the `modules/` directory that are also used in the build.

When the source root directory is set one level up (e.g. `zephyrproject/`), it picks up the `modules/` and other directories.
However, at least for the sample build I did for the `blinky` project on an Adafruit Feather STM32F405 Express, some of the included modules contained invalid `SPDX-License-Identifier:` tags.
For the proof of concept, the license identifier scanner is not smart enough to distinguish these invalid tags, so it incorporates them into the SPDX document in ways that cause it to be invalid.

Here are a few examples:
* [`hal/nxp/mcux/devices/MK22F51212/MK22F51212.xml`](https://raw.githubusercontent.com/zephyrproject-rtos/hal_nxp/master/mcux/devices/MK22F51212/MK22F51212.xml):
  * contains the line `SPDX-License-Identifier: BSD-3-Clause</licenseText>`
  * although this is valid XML, having the `</licenseText>` closing tag appear on the same line as the short-form identifier causes it to get incorporated into the identifier
  * ideally, the closing tag should be split onto a subsequent line
* [`hal/nxp/mcux/drivers/imxrt6xx/fsl_dsp.h`](https://github.com/zephyrproject-rtos/hal_nxp/blob/master/mcux/drivers/imxrt6xx/fsl_dsp.h):
  * contains the line `SPDX-License-Identifier: BS`
  * `BS` is not a valid identifier on the [SPDX License List](https://spdx.org/licenses)
  * looks like it was perhaps a cut-off version of `BSD-3-Clause` or another BSD license ID; note that [`fsl_dsp.c`](https://github.com/zephyrproject-rtos/hal_nxp/blob/master/mcux/drivers/imxrt6xx/fsl_dsp.c) is `BSD-3-Clause`
* [`mcuboot/ext/nrf/cc310_glue.c`](https://github.com/zephyrproject-rtos/mcuboot/blob/master/ext/nrf/cc310_glue.c) and [`cc310_glue.h`](https://github.com/zephyrproject-rtos/mcuboot/blob/master/ext/nrf/cc310_glue.h):
  * contains the line `SPDX-License-Identifier: LicenseRef-BSD-5-Clause-Nordic`
  * this is a correct format for an SPDX reference to a license that is not on the license list (see [here](https://spdx.github.io/spdx-spec/6-other-licensing-information-detected/) and [here](https://spdx.github.io/spdx-spec/appendix-IV-SPDX-license-expressions/))
  * however, the `LicenseRef-` also needs to be defined somewhere in the repo, and I don't see where it is currently defined or where a copy of the license text appears
  * note that cmake-spdx would also need to be improved to be able to incorporate user-defined license sections
  * it looks like https://github.com/spdx/license-list-XML/issues/689 may be referring to the license in question here
    * if so, Zephyr may want to consider whether to continue distributing software under this license, as it would likely not be considered an open source license (due to limitations on redistributing or using the binary software other than for Nordic ASA circuits)
* [`openthread/third_party/NordicSemiconductor/libraries/nrf_security/include/mbedtls/ccm_alt.h`](https://github.com/zephyrproject-rtos/openthread/blob/zephyr/third_party/NordicSemiconductor/libraries/nrf_security/include/mbedtls/ccm_alt.h):
  * contains the text `SPDX-License-Identifier: BSD-3-Clause OR Arm’s non-OSI source license`
  * the second part of this expression (after the `OR`) is not valid
  * it should instead use the `LicenseRef-` format described above, along with a definition of the corresponding license text
