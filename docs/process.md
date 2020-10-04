# Process for using cmake-spdx

The following documents the current process for using the cmake-spdx proof-of-concept to generate SPDX documents.

## Step 1: Set up Zephyr for building sample blinky project

For this proof of concept, I built the [`samples/basic/blinky`](https://github.com/zephyrproject-rtos/zephyr/tree/master/samples/basic/blinky) project that is included in the Zephyr sources.

Specifically, I followed many of the instructions in [this Adafruit tutorial](https://learn.adafruit.com/blinking-led-with-zephyr-rtos/overview) to configure the Zephyr build environment.
The `blinky` program was configured to build on an [Adafruit Feather STM32F405 Express](https://www.adafruit.com/product/4382).

## Step 2: Run CMake configured to build with file API responses

CMake includes a [file-based API](https://cmake.org/cmake/help/v3.18/manual/cmake-file-api.7.html) which can output a collection of JSON files with information about a CMake build process.
This information includes details about targets, dependencies, and relevant directories and files.
In particular, it includes some (though likely not all) information about which source files are built into which binary outputs.

Before running `west build` at the build step in the [Adafruit tutorial](https://learn.adafruit.com/blinking-led-with-zephyr-rtos/building-a-sample-program), I first configured the CMake file-based API to run for the build.
This was done by creating an empty file in a Zephyr `build/` directory prior to running the build:

```
> mkdir -p .cmake/api/v1/query
> touch .cmake/api/v1/query/codemodel-v2
```

See [here](https://cmake.org/cmake/help/latest/manual/cmake-file-api.7.html#v1-shared-stateless-query-files) for more details about triggering the CMake file API.

Then, run the build with `west build` as usual:

```
> west build -p auto -b adafruit_feather_stm32f405 samples/basic/blinky
```

CMake builds as usual, and because of the presence of the empty codemodel-v2 file, CMake generates JSON files with the build / target data at `.cmake/api/v1/reply/`.

The JSON files from the build are available in this repo in the [`/example/api-example-reply/api/v1/reply/`](/example/api-example-reply/api/v1/reply) directory.

## Step 3: Run cmake-spdx to create SPDX documents

Now that the build is complete and we have the metadata from the CMake API JSON files, we can process them to create SPDX documents corresponding to the build.

cmake-spdx takes the following arguments:

```
python3 main.py <path-to-cmake-api-index.json> <path-to-top-level-sources> <spdx-output-dir> <spdx-namespace-prefix>
```

For the proof-of-concept run, I called it with:

```
> python3 main.py api-example-reply/api/v1/reply/index-2020-08-29T18-34-19-0138.json /home/steve/programming/zephyr/zephyrproject/ ./scratch/ https://swinslow.net/zephyr/
```

The arguments are:
* _path-to-cmake-api-index.json_: `api-example-reply/api/v1/reply/index-2020-08-29T18-34-19-0138.json`: This is the path to the `index-\*.json` file in the `reply` directory from the CMake api response.
  * This index file contains a pointer to the `codemodel-\*.json` file which is the real "table of contents" for the API response.
  * The index file should be used as the starting point for making use of the CMake file API's response data. (See [here](https://cmake.org/cmake/help/latest/manual/cmake-file-api.7.html#v1-reply-index-file): "Clients must read the reply index file first and may read other v1 Reply Files only by following references.")
* _path-to-top-level-sources_: `/home/steve/programming/zephyr/zephyrproject/`: This is the path to the top-level directory containing all of the relevant sources.
  * Ideally, this would not be a parameter that the user needs to pass, but should be derivable from following the various directory metadata in the CMake file API codemodel response.
  * See https://github.com/swinslow/cmake-spdx/issues/4 for a more specific discussion of this.
* _spdx-output-dir_: `./scratch/`: This is the directory where cmake-spdx should output the generated SPDX documents.
* _spdx-namespace-prefix_: `https://swinslow.net/zephyr/`: This is a prefix that will be used to create the SPDX namespace for each of the generated documents.
  * See [the SPDX spec](https://spdx.github.io/spdx-spec/2-document-creation-information/#25-spdx-document-namespace) for more information about the purpose and format of SPDX document namespaces.

## Output

cmake-spdx will create two SPDX documents:
* [`sources.spdx`](/example/sources.spdx): an SPDX document for the files used as sources for the build.
* [`build.spdx`](/example/build.spdx): an SPDX document for the files resulting from the build.

cmake-spdx will also output errors encountered.
In particular, from this proof-of-concept run, it outputs a few errors indicating failures to generate SPDX Relationship records for a few of the built files.

## Next steps

See [`internals.md`](/docs/internals.md) for a discussion of what cmake-spdx is doing behind the scenes.

See [`next-steps.md`](/docs/next-steps.md) for details about what is not currently working in this proof of concept, and areas for improvement.
