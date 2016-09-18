## How Does This Package Work?

- Use directory structure to indicate version
   - v1.2.60 corresponds to directory: `src/proto3/1/2/60`
- The directory containing all `*.proto` files should remain flat
  `src/proto3/1/2/60/mything` should never exist.
   - If a use case for that arrises, this rule may change.
- Enforce versions through well structured release and deployment

### Makefile

- The process of compiling the `proto` files into language specific
  `protobuf` objects and release bundling is handled by the top level
  Makefile.

-

### Python Releases

**Intro**

- The python module should be in the form: `{{cookiecutter.model_namespace}}``
  - All of the generated modules will be then imported as such: `from
    {{cookiecutter.model_namespace}} import myproto_pb2`

- `{{cookiecutter.project_namespace}}` is a namespace package
  - This is to allow for a common namespace for all of our potential
      services. This allows service models to exist in different repos
      and go through more granular releases.

**Nitty Gritty**

- `make MODEL_VERSION=$VERSION release` will find the `*.proto` files
  in the `src/proto3` directory that correspond to that version (see
  How Does This Package Work).
  - You can generate the files without a release using `make
    MODEL_VERSION=$VERSION compile`.
- It then invokes `protoc` on those files with cli arguments
  specifying we want the generated python modules to be output into
  `build/`. The `build/` directory is created if it does not exist. At
  this point, the generated python modules will be located directly
  under `build/` and will not be part of a proper python module.
- A special python script `python/bin/release.py` is called
  with a subset of the Makefile arguments, such as the version. The
  purpose of `release.py` is to build the proper module
  directory structure and generate a `setup.py` so it can be compiled
  into an installable _egg_, _wheel_, or _tarball_.
- prepare-release
