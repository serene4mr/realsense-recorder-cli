python -m nuitka \
  --standalone \
  --onefile \
  --remove-output \
  --include-package=src \
  --static-libpython=no \
  --output-dir=build/output \
  realsense-recorder-cli.py