In "~/.openclaw/" directory, run command `curl -fsSL https://openclaw.ai/install.sh | bash -s -- --no-onboard`. 

Notice that it will create a directory *"/home/robot/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/dist/"*,
but no *"/home/linuxbrew/.linuxbrew/lib/node_modules/openclaw"*.

~~~
robot@robot-test:~$ curl -fsSL https://openclaw.ai/install.sh | bash -s -- --no-onboard

  🦞 OpenClaw Installer
  I can't fix your code taste, but I can fix your build and your backlog.

✓ Detected: linux

Install plan
OS: linux
Install method: npm
Requested version: latest
Onboarding: skipped

[1/3] Preparing environment
✓ Node.js v24.14.0 found
· Active Node.js: v24.14.0 (/home/robot/.nvm/versions/node/v24.14.0/bin/node)
· Active npm: 11.9.0 (/home/robot/.nvm/versions/node/v24.14.0/bin/npm)

[2/3] Installing OpenClaw
✓ Git already installed
· Installing OpenClaw v2026.3.23-2
✓ OpenClaw npm package installed
✓ OpenClaw installed

[3/3] Finalizing setup

🦞 OpenClaw installed successfully (OpenClaw 2026.3.23-2 (7ffe7e4))!
Installation complete. Your productivity is about to get weird.

· Skipping onboard (requested); run openclaw onboard later

FAQ: https://docs.openclaw.ai/start/faq


robot@robot-test:~$ ls -l /home/robot/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/
total 1080
drwxrwxr-x   3 robot robot   4096 Mar 25 21:48 assets
-rw-rw-r--   1 robot robot 829155 Mar 25 21:48 CHANGELOG.md
drwxrwxr-x  13 robot robot  69632 Mar 25 21:48 dist
drwxrwxr-x  25 robot robot   4096 Mar 25 21:48 docs
-rw-rw-r--   1 robot robot   1074 Mar 25 21:48 LICENSE
drwxrwxr-x 317 robot robot  12288 Mar 25 21:48 node_modules
-rwxrwxr-x   1 robot robot   3818 Mar 25 21:48 openclaw.mjs
-rw-rw-r--   1 robot robot  42913 Mar 25 21:48 package.json
-rw-rw-r--   1 robot robot 122976 Mar 25 21:48 README.md
drwxrwxr-x  53 robot robot   4096 Mar 25 21:48 skills

robot@robot-test:~$ ls /home/robot/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/dist/plugin-sdk/plugin-*
plugin-entry.d.ts    plugin-entry.js      plugin-runtime.d.ts  plugin-runtime.js  

robot@robot-test:~$ ls -l /home/linuxbrew/.linuxbrew/lib/node_modules/openclaw
ls: cannot access '/home/linuxbrew/.linuxbrew/lib/node_modules/openclaw': No such file or directory
~~~
