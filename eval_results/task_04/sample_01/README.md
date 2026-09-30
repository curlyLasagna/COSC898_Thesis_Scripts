# Clang (C/C++) and Build Tools Project

## Environment Activation
Enter the reproducible Nix development shell:
```bash
nix develop
```

## Verify Installed Tools
```bash
clang --version
clang++ --version
cmake --version
make --version
```

## Build Instructions

### Option 1: Using CMake
```bash
cmake -B build -S .
cmake --build build
./build/app
```

### Option 2: Using Make
```bash
make
./app
```
