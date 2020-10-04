# cmake-spdx

## What is it?

cmake-spdx is a tool to automatically generate SPDX documents as software bill-of-materials (SBOM) manifests corresponding to the sources and build artifacts from a CMake build process.

It was created with a particular focus for [Zephyr](https://www.zephyrproject.org/) using the [west build tool](https://docs.zephyrproject.org/latest/guides/west/index.html).
(Zephyr / west are the only context I've actually tested it in so far.)
However, nothing in here is Zephyr- or west-specific, so there's no reason that it wouldn't work for any other project that uses CMake for builds.

Note that cmake-spdx is still a very early-stage tool and should be treated as a proof of concept rather than anything more production-ready.

## What does it do?

cmake-spdx leverages the [CMake file-based API](https://cmake.org/cmake/help/latest/manual/cmake-file-api.7.html) to observe and parse data about a CMake build process.
It then translates that data, together with a scan of the relevant code directories, to create two SPDX files:

* `sources.spdx`, describing the source files; and
* `build.spdx`, describing the built artifacts.

It uses the CMake API metadata to determine which source files are built into which binary artifacts, and creates [SPDX relationships](https://spdx.github.io/spdx-spec/7-relationships-between-SPDX-elements/) to document them in a machine-readable and human-readable manner.

The scanning process also looks for [SPDX short-form identifiers](https://spdx.dev/ids) as license information in the code, and records any that are found.

Examples of the generated files for a sample run can be found at [`example/sources.spdx`](/example/sources.spdx) and [`example/build.spdx`](/example/build.spdx).
A description of the process that was used for generating these files can be found in [process.md](/docs/process.md).

## More details

See the following documents for more details:
* [process.md](/docs/process.md): how to use cmake-spdx
* [internals.md](/docs/internals.md): more details about how cmake-spdx does what it does
* [next-steps.md](/docs/next-steps.md): bugs and areas for improvement

## License

Apache-2.0
