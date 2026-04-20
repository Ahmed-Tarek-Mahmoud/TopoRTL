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

		await runWithUserPython(output, scriptsDir, pythonScript, rtlDir, outputFile);
	});


	context.subscriptions.push(sortDisposable);
}

async function runWithUserPython(
	output: vscode.OutputChannel,
	scriptsDir: string,
	pythonScript: string,
	rtlDir: string,
	outputFile: string
) {
	try {
		output.appendLine(`\nStarting RTL dependency resolution...`);
		output.appendLine(`RTL Directory: ${rtlDir}`);
		output.appendLine(`Output File: ${outputFile}`);
		output.appendLine(`Platform: ${process.platform}`);

		let pythonExe: string;

		// Try to find Python in the system PATH
		try {
			execSync('python --version', { stdio: 'pipe' });
			pythonExe = 'python';
		} catch {
			try {
				execSync('python3 --version', { stdio: 'pipe' });
				pythonExe = 'python3';
			} catch {
				const platformMsg = process.platform === 'win32' 
					? 'Python is not installed. Please download and install Python 3.7+ from https://www.python.org/downloads/ and ensure it is added to your PATH.'
					: 'Python is not installed. Please install Python 3.7+ (e.g., apt-get install python3 on Linux or brew install python3 on macOS).';
				vscode.window.showErrorMessage(platformMsg);
				output.appendLine(`ERROR: ${platformMsg}`);
				return;
			}
		}

		// Run the main Python script
		output.appendLine(`Using Python: ${pythonExe}`);
		
		// Verify the python executable can run
		try {
			const versionCheck = execSync(`"${pythonExe}" --version`, { encoding: 'utf-8' });
			output.appendLine(`Python version: ${versionCheck.trim()}`);
		} catch (e: any) {
			output.appendLine(`WARNING: Could not verify Python version: ${e.message}`);
		}

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
