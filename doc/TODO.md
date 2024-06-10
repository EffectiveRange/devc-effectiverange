# Minimum Viable Product for Demo requirements:

- Single page app (SPA) for:
  - select active device(s) manually
  - issue manual launch command

- Device Discovery Service (DDS):
  - for detecting devices on a network
  - implemented in python

- Ansible Dynamic Inventory Plugin:
  - using DDS, for managing devices

- Ansible playbooks:
  - deployment (initial, or upgrade) to edge devices

- pi-gen: image generator for installable pi images:
  - setup dynamic hostname using the CPU serial number
  - The DDS service must be preinstalled/configured
  - The BerryLan nymea-manager, for configuring WiFi access using bluetooth
  - Pre-install required kernel modules and conigure the required overlay (i2s + mic driver)
  - Pre-install role-descriptor json

- Open API specification for:
  - register device ()
  - health check ()
  - set active device()  (two-fold, 1 for business logic, 1 for the actual devices)
  - launch command()
  - authentication APIs
  - enumerate devices()
  - set_launch_sensitivity ()
  - set_pulse_width()

- Backend Business logic:
  - trigger deployment playbook upon register
  - periodic health check for known devices
  - mic sensitivty calibration
  - pulse width calibration

- Backend Env:
  - backend application hosting (docker, procedures, mechanisms)
  - CI pipeline setup for backend testing/docker building

- Devenv:
  - amd64 seamless build
  - apt repository hosting (local + prod)
  - dev publish mechanism (cmake integration + TODO: check python deployment)
  - setup conan for source only dependencies

- HW:
  - 2 sets of devices 2x (1 with stereo mic + 1 with relay ) + 1 wifi router + laptop/pc + 9V battery + light bulb
  - protopye box assembly
  - microphone stand
  - microphone funnel

