# Node.js (LTS) Development Environment

A reproducible development environment configured with Node.js LTS (`nodejs_22`) and `npm` using Nix Flakes.

## Environment Activation

Enter the reproducible development shell using Nix:

```bash
nix develop
```

Or allow direnv if `.envrc` is used:

```bash
direnv allow
```

Upon entering the shell, `node` and `npm` are available in your PATH.

## Verify Installed Tools

Verify the installed Node.js and npm versions:

```bash
node --version
npm --version
```

## Running the Project

Install dependencies:

```bash
npm install
```

Run the entry point:

```bash
node index.js
```
