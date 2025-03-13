# Effective Range

## Bootstrapping new target

- install image on SD card, and boot up RPi device
- create a new directory under `mkdir TARGET/<target name>`
- use `./scripts/collect_info <hostname> > TARGET/<target name>/target` to collect runtime version information
- the `TARGET/<target name>/target.extra` can contain extra environment variables that are sourced by the cross tools build scripts
- retrieve kernel config (see section below)
- add any potential patches that needed to be applied when building the cross compiler toolchain

### Retrieving Kernel Config from a Running Device

To retrieve the kernel configuration from a running device, you can use the following command:

```sh
ssh <device> "cat /boot/config-\$(uname -r) " > TARGET/<target name>/.config
```

This command will extract the kernel configuration and save it locally.


