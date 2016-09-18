# {{cookiecutter.repo_name}}

Protobuf Service Models {{cookiecutter.project_name}}

## Modifying Service Models

### Pull Request and Versioning

- Insert RFC snippets and best practices
- TBD

### Building your Release Candidate

- `VERSION=<your-version>`
- `RC=rc1`
- `make MODEL_VERSION=$VERSION RELEASE_SUFFIX=$RC release`
- `git push -u origin release-python-$(VERSION)-$RC`
- Create a release on github
  - Ensure you have clicked `[x] Pre-Release`
- Verify it is pip installable: `pip install --upgrade git+ssh://{{cookiecutter.repo_url}}@$VERSION-$RC`

### Testing

- Ensure dependent services have their requirements updated to reflect
  the new version number before testing.
- For backend, you will need to rebuild the virtualenv with `make
  bootstrap`.

### Releasing

- `VERSION=<your-version>`
- `make MODEL_VERSION=$VERSION RELEASE_SUFFIX=$RC release`
- `git push -u origin release-python-$(VERSION)`
- Create a release on github
- Verify it is pip installable: `pip install --upgrade git+ssh://{{cookiecutter.repo_url}}$VERSION-$RC`
