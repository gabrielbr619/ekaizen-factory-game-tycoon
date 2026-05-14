import { existsSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawn } from 'node:child_process'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const backendDir = resolve(scriptDir, '../../backend')
const winPython = resolve(backendDir, '.venv/Scripts/python.exe')

const candidates =
  process.platform === 'win32' && existsSync(winPython)
    ? [{ command: winPython, args: ['-m'] }]
    : process.platform === 'win32'
      ? [{ command: 'py', args: ['-3', '-m'] }]
      : [{ command: 'python3', args: ['-m'] }, { command: 'python', args: ['-m'] }]

function start(index) {
  const candidate = candidates[index]
  if (!candidate) {
    throw new Error('No Python runtime available for backend E2E server.')
  }
  const child = spawn(
    candidate.command,
    [...candidate.args, 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'],
    {
      cwd: backendDir,
      env: {
        ...process.env,
        DATABASE_PATH: resolve(backendDir, 'data/e2e-factory-game.sqlite3'),
      },
      stdio: 'inherit',
    },
  )
  child.on('error', () => start(index + 1))
  child.on('exit', (code) => {
    process.exit(code ?? 1)
  })
}

start(0)

