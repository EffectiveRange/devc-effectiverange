# Dev container design

The problem is that no distribution is available for amd64 that embedded device runs, therefore
matching package versions can't be installed.

## Dependency managements 

For native compiled software we differentiate 4 kinds of dependency:
- build-only
- source-only
- static library
- runtime library

Build-only dependencies can be obtained from any sources given it's supports automation (pip, conan, apt, etc.). Source only dependencies will be using the Conan package manager, for header `NOTE: this is not added yet, will be added when first needed`


## Collecting dependency info from a RPI installation

The TARGET dir layout is the following:
- `<TARGET Name>`
  - target  `the TARGET file, obtained by the collect_info script, could be edited manually, contains important OS & version info environment variables`
  - target.extra `extra env variables to be addded manually`
  - .config  `the kernel config settings, required for setting up the kernel build infra`
  - patch `contains patch files with a number prefixed that controls the application order`
    - id-dirname.patch `patch file name <idx>-<dirname>.patch will be applied in directory <dir>, e.g. 11-gcc.patch`
   

### Setting up a new TARGET and building the devcontainer

1. create a new directory as detailed above for the new TARGET
2. Use `scripts/collect_info <hostname> > path/to/TARGETDIR/target` to save the main target file 
3. Optionally add any custom variable to `target.extra` file
4. TBD: how to obtain the kernel config file...
5. execute `make <target>` from the workspace root


### Development 

For interactive development, you can use the `dev_tools/run_devc` command, that accepts the container id as argument. It will mount in the directory into the running container. Inside the container shell, you can use the `/devc/dev_tools/link_devc <TARGET name>` command to set up symlinks inside the container to the current workspace TARGET files, that can be editet on the fly from the host, without the need of rebuilding the container.


## Build details

The top level entry point is the `scripts/build_all[_$ARCH]` which is executed from the Dockerfile when building the container. Any common build package dependency should be listed in `scripts/packages` file. 
### Unified build container layout

### Details
The build_all script invokes the `build_cross_tools` script, that in turn executes the build steps from `scripts/build_steps_armhf` in order. The build steps are - and should be - written in a way so that they are individually executable for easier troubleshooting. E.g. while troubleshooting a build and there's an error at one step you can invoke
```bash
root@1231a9c601e7:/tmp/build#/home/crossbuilder/scripts/build_steps_armhf/80-kernelmodulebuildstep /home/crossbuilder/target
```
Note: the TARGET dir has to be passed in for each build step for the environment variables

After successful docker image build, all unnecessary deps are removed, also the build artifact directory as well. The full build log is kept under `/tmp/build.log` so that in case of a failure it can be inspected later.


## Build environment

### C++ software

The runtime dependencies, that are also required during build time are installed using the `dpkgdeps` tooling. This tool supports multi-arch package installation. See tooling help for more details. `dpkgdeps` will look for deps.json files recursively, and will install the summarized dependencies in the build chroot environment using the native package manager. After the dependencies are collected, a manifest file is generated with the concrete versions of the dependencies installed. This manifest file can be used later to recreate the same build with the same versions`NOTE: this mechanism is not yet implemented, but it should be added for reproducible builds. TODO: implement the manifest mechanism`.

 There's a cmake frontend function added for the dpkgdeps utility, integrated into the `ER_ADD_EXECUTABLE` function. This function is just a front-end to standard cmake `ADD_EXECUTABLE` function, but installs the deps during configuration through the `dpkgdeps` tool. After the target is defined, the ordinary cmake standard functions can be used for adding include dependencies, library dependencies, etc. See `test/build_exe_test` for a complete example.

 Similarly to add executable, for libraries the `ER_ADD_SHARED_LIBRARY` and the `ER_ADD_STATIC_LIBRARY` functions can be used

A  basic project file structure should look like:
- Project dir/
  - CMakeLists.txt
  - deps.json - optional
  - include/  - optional, for libraries
  - include_priv/ - optional, for private include header files
  - src/ - source files directory

Currently the packaging does not handle well the sub-directory cmake build files, as only the last defined project artifacts are packaged. Later on this should also be addressed, but we can interface with our own software through the build sysroot via installation. (e.g: install the cmake project then another project can pick it up through the sysroot)

For C++ unit tests use the `ER_ENABLE_TEST()` macro for enabling the unit test only when the target architecture matches the host.(i.e. to not try to run armhf executables on x86_64)

 ## Packaging

 ### C++ software

Targets added through the `ER_` cmake functions will have support for automatic packaging. That means all the runtime dependencies will be added as deb package dependencies, with explicit version specifier (in the future, for now it's only the dependency package name is added).
For library projects the public include directory is automatically packaged.
If any other file is needed to be packaged, then it should have an install target directive (NB: in the future we might integrate convenince packaging into the scripts) 