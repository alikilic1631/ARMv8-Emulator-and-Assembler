# ARMv8 Project

## Repository structure

- `.editorconfig`: Ensure everyone is using consistent text editor settings.
- `.gitlab-ci.yml`: Run tests using GitLab CI, so that merge requests are easier to review.
  This removes the need to review a merge request locally, you can just view tests in the GitLab UI.

### `src/`
- Source C (and C header) files for `emulate` and `assemble`.
- Extension is merged into parts 1 and 2, since all tests pass.
- `Makefile` for building.

#### `programs/led_blink.s`
- Code for part 3 (blinking an LED on a Raspberry Pi).
- Uses GPIO pin 2.
- Memory addresses for GPIO pins are _not_ loaded immediately since:
  1. They don't fit into some `imm` fields.
  2. Labels make it clearer.

### `doc/`
- Source latex files for checkpoint and final reports.
- `Makefile` for building.

### `armv8_testsuite/`
- A copy of the [armv8_testsuite](https://gitlab.doc.ic.ac.uk/teaching-fellows/armv8_testsuite).
- **Why not a git submodule?** The testsuite requires authorisation, and since people clone in different ways (SSH or HTTPS),
  the submodule is a bit fiddly to get working. Furthermore it could make CI more diffuclt. Therefore, easier to just copy it.
- **Why is this needed at all?** The GitLab CI requires access to test files, and as described above, the easiest way to
  achieve that is to include the test files in the repository, by having a copy of the testsuite in the repository.