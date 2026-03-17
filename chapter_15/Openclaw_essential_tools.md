# Openclaw Essential Tools

## 1. Objective

This chapter is a step-by-step tutorial on the installation and usage of some essential tools of Openclaw, including

* [QMD](https://github.com/tobi/qmd)

* Live Chrome session attach

* Search

&nbsp;
## 2. Environment

## 2.1 Create a new user

~~~
root# useradd -m -s /usr/bin/bash claw_team
root# passwd claw_team
  New password: W**T**
  Retype new password: W**T**
  passwd: password updated successfully
  
root# usermod -aG sudo claw_team  
  
root# su - claw_team
  To run a command as administrator (user "root"), use "sudo <command>".
  See "man sudo_root" for details.

# From 'root' switches to 'claw_team'
claw_team$ 
~~~

## 2.2 Install npm

~~~
# Download and install nvm:
claw_team$ curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash

# in lieu of restarting the shell
claw_team$ \. "$HOME/.nvm/nvm.sh"

# Download and install Node.js:
claw_team$ nvm install 24

# Verify npm version:
claw_team$ npm --version
11.9.0
claw_team$ node --version
v24.14.0

# Install pnpm
claw_team$ curl -fsSL https://get.pnpm.io/install.sh | sh -
  ==> Downloading pnpm binaries 10.32.0
  ...
  To start using pnpm, run:
  source /home/claw_team/.bashrc

claw_team$ source /home/claw_team/.bashrc
claw_team$ which pnpm
  /home/claw_team/.local/share/pnpm/pnpm
~~~

## 2.3 Install brew

~~~
claw_team$  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  ==> Checking for `sudo` access (which may request your password)...
  ==> This script will install:
  /home/linuxbrew/.linuxbrew/bin/brew
  /home/linuxbrew/.linuxbrew/share/doc/homebrew
  ...
  ==> Next steps:
  - Run these commands in your terminal to add Homebrew to your PATH:
      echo >> /home/claw_team/.bashrc
      echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)"' >>   
      /home/claw_team/.bashrc
      eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)"
  - Install Homebrew's dependencies if you have sudo access:
      sudo apt-get install build-essential
    For more information, see:
      https://docs.brew.sh/Homebrew-on-Linux
  ==> Running `brew cleanup gcc`...
  Disable this behaviour by setting `HOMEBREW_NO_INSTALL_CLEANUP=1`.
  Hide these hints with `HOMEBREW_NO_ENV_HINTS=1` (see `man brew`).
      
claw_team$ echo >> /home/claw_team/.bashrc
claw_team$ echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)"' >> /home/claw_team/.bashrc
claw_team$ eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)"

claw_team$ sudo apt-get install build-essential  

claw_team$ brew install gcc
  ==> Fetching downloads for: gcc
  ...
~~~



&nbsp;
## 3. QMD (Query Markup Documents)

We followed the instructon of ["3 Essential Tools for OpenClaw"](https://x.com/_sean_matthew/status/2028902126005653889), 
but didn't use ClaudeCode. 

Additionally, notice that we use an alibaba ECS located in Virginia, US, so that we don't need to handle the GFW issue. 

~~~
Set up QMD as the memory backend for my OpenClaw agent.
Follow the official docs here:
https://docs.openclaw.ai/concepts/memory#qmd-backend-experimental

Make sure to:
1. Install the QMD CLI
2. Install SQLite with extension support if needed
   (macOS: brew install sqlite)
3. Configure memory.backend = "qmd" in my openclaw.json
4. Add my workspace memory files as a QMD collection
5. Run the initial embed so models are downloaded and
   the index is built
6. Verify it works by running a test query
~~~

&nbsp;
## 3.1 

~~~

~~~
