// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { execSync } from 'child_process';

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
	
	const output = vscode.window.createOutputChannel('Testbench Assistant');
	output.show(true);
	output.appendLine('"TopoRTL" is now active!');
	const config = vscode.workspace.getConfiguration('toportl');

	// Register the Sort command
	const sortDisposable = vscode.commands.registerCommand('toportl.sort', async () => {
		const workspaceFolders = vscode.workspace.workspaceFolders;
		if (!workspaceFolders) {
			vscode.window.showErrorMessage('No workspace folder open');
			return;
		}

		const extensionRoot = context.extensionPath;
		const scriptsDir = path.join(extensionRoot, 'src', 'Scripts');
		const pythonEnvDir = path.join(extensionRoot, 'src', 'python_env');
		const pythonScript = path.join(scriptsDir, 'main.py');

		// Show open dialog to select RTL directory
		const uris = await vscode.window.showOpenDialog({ 
			canSelectFolders: true, 
			openLabel: 'Select RTL directory',
			title: 'Select RTL source directory'
		});

		if (!uris || uris.length === 0) return;

		const rtlDir = uris[0].fsPath;
		const outputFile = path.join(rtlDir, 'src_files.list');

		await runWithBundledPython(output, scriptsDir, pythonEnvDir, pythonScript, rtlDir, outputFile);
	});


	context.subscriptions.push(sortDisposable);
}

async function runWithBundledPython(
	output: vscode.OutputChannel,
	scriptsDir: string,
	pythonEnvDir: string,
	pythonScript: string,
	rtlDir: string,
	outputFile: string
) {
	try {
		output.appendLine(`\nStarting RTL dependency resolution...`);
		output.appendLine(`RTL Directory: ${rtlDir}`);
		output.appendLine(`Output File: ${outputFile}`);
		output.appendLine(`Platform: ${process.platform}`);

		const isWindows = process.platform === 'win32';
		let pythonExe: string;

		if (isWindows) {
			// Windows: Use bundled Python environment
			output.appendLine(`Python Env Dir: ${pythonEnvDir}`);
			
			if (!fs.existsSync(pythonEnvDir)) {
				vscode.window.showErrorMessage('Bundled Python environment not found. Please ensure python_env folder exists.');
				return;
			}

			pythonExe = path.join(pythonEnvDir, 'Scripts\\python.exe');

			if (!fs.existsSync(pythonExe)) {
				vscode.window.showErrorMessage(`Python executable not found at ${pythonExe}`);
				return;
			}
		} else {
			// Linux/Mac: Use system Python
			pythonExe = 'python3';
			
			try {
				execSync(`${pythonExe} --version`, { stdio: 'pipe' });
			} catch {
				pythonExe = 'python';
				try {
					execSync(`${pythonExe} --version`, { stdio: 'pipe' });
				} catch {
					vscode.window.showErrorMessage('Python is not installed. Please install Python 3.7+');
					return;
				}
			}
		}

		// Run the main Python script
		output.appendLine(`Using Python from: ${pythonExe}`);
		output.appendLine(`Running main.py...`);
		try {
			const result = execSync(
				`"${pythonExe}" "${pythonScript}" "${rtlDir}" "${outputFile}"`,
				{ cwd: scriptsDir, encoding: 'utf-8' }
			);
			output.appendLine(result);
			output.appendLine(`\nSuccess! Generated ${outputFile}`);
			vscode.window.showInformationMessage(`RTL dependency resolution complete. Output: ${outputFile}`);
		} catch (error: any) {
			output.appendLine(`Error running main.py: ${error.message}`);
			if (error.stdout) output.appendLine(`STDOUT: ${error.stdout}`);
			if (error.stderr) output.appendLine(`STDERR: ${error.stderr}`);
			vscode.window.showErrorMessage('Failed to run RTL dependency resolution. Check output for details.');
		}
	} catch (error) {
		output.appendLine(`Unexpected error: ${error}`);
		vscode.window.showErrorMessage('Unexpected error during RTL processing');
	}
}

// This method is called when your extension is deactivated
export function deactivate() {}
