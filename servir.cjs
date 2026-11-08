const { spawn } = require('child_process');
const path = require('path');

const python = process.env.PYTHON || 'python';
const app = spawn(python, [path.join(__dirname, 'backend', 'app.py')], {
  cwd: __dirname,
  stdio: 'inherit'
});

app.on('error', error => {
  console.error(`Não foi possível iniciar Python (${python}): ${error.message}`);
  process.exitCode = 1;
});

app.on('exit', (code, signal) => {
  if (signal) {
    console.log(`Backend terminado (${signal}).`);
  } else if (code) {
    console.error(`Backend terminou com código ${code}.`);
    process.exitCode = code;
  }
});

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => {
    if (!app.killed) app.kill(signal);
  });
}
