# TopoRTL

A VS Code extension that integrates the RTL Dependency Resolver, allowing you to analyze SystemVerilog/Verilog RTL files and generate a correctly ordered compilation list (`src_files.list`) directly from the editor.

## Features

- **RTL File Discovery**: Automatically finds all `.v`, `.sv`, and `.svh` files in the selected directory and its subdirectories.
- **Dependency Analysis**: Parses RTL files to extract modules, interfaces, packages, imports, and includes.
- **Topological Sorting**: Generates a `src_files.list` file with files ordered for correct compilation.
- **Cycle Detection**: Identifies and reports circular dependencies.
- **Integrated Workflow**: Seamlessly integrates with VS Code for easy access without leaving the editor.

## Requirements

- VS Code 1.110.0 or later
- **Python 3.6 or later** must be installed and accessible from your system PATH

### Platform-Specific Installation

**Windows**: 
1. Download Python 3.7+ from https://www.python.org/downloads/
2. **Important**: During installation, check "Add Python to PATH"
3. Restart VS Code after installation

**macOS**: Python 3 is usually pre-installed. If needed: `brew install python3`

**Linux**: Install via package manager (e.g., `sudo apt-get install python3` on Ubuntu)

## How to Use

1. **Install the Extension**: Install TopoRTL from the VS Code Marketplace or by sideloading the `.vsix` file.

2. **Open Your RTL Project**: Open a workspace or folder containing your RTL source files in VS Code.

3. **Run the Sort Command**:
   - Open the Command Palette (`Ctrl+Shift+P` on Windows/Linux, `Cmd+Shift+P` on macOS).
   - Type and select `TopoRTL: Sort`.
   - A dialog will appear to select the RTL directory. Choose the root directory of your RTL project.

4. **View Results**: The extension will analyze the files and generate a `src_files.list` file in the selected directory. The output will be displayed in the "Testbench Assistant" output channel.

## Extension Settings

This extension does not currently expose any user-configurable settings.

## Known Issues

- Ensure that the selected directory contains valid RTL files (`.v`, `.sv`, `.svh`).
- The extension may take time to process large RTL projects.

## Release Notes

### 0.0.1

- Initial release
- Basic RTL dependency resolution and file list generation

---

## Following Extension Guidelines

This extension follows VS Code extension best practices. For more information, see the [Extension Guidelines](https://code.visualstudio.com/api/references/extension-guidelines).

## Working with Markdown

You can author your README using Visual Studio Code. Here are some useful editor keyboard shortcuts:

- Split the editor (`Cmd+\` on macOS or `Ctrl+\` on Windows and Linux).
- Toggle preview (`Shift+Cmd+V` on macOS or `Shift+Ctrl+V` on Windows and Linux).
- Press `Ctrl+Space` (Windows, Linux, macOS) to see a list of Markdown snippets.

## For More Information

- [VS Code's Markdown Support](http://code.visualstudio.com/docs/languages/markdown)
- [Markdown Syntax Reference](https://help.github.com/articles/markdown-basics/)

**Enjoy!**
