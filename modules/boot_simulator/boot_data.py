"""Accurate boot-phase data for Windows and Linux.

Kept separate from the UI so the same facts can later feed the Learning Center,
Search, and quizzes without duplication (Single Responsibility).
"""
from dataclasses import dataclass
from typing import List, Dict


@dataclass(frozen=True)
class BootStage:
    order: int
    name: str
    component: str
    summary: str
    key_files: List[str]
    security_note: str


WINDOWS_BOOT: List[BootStage] = [
    BootStage(1, "Power-On & POST", "UEFI/BIOS Firmware",
              "The firmware runs a Power-On Self Test, initialises CPU, RAM and "
              "buses, then hands off to the boot device selected in NVRAM.",
              ["UEFI firmware (SPI flash)"],
              "Firmware implants (e.g. bootkits) live below the OS and survive "
              "reinstalls. Secure Boot verifies signatures before execution."),
    BootStage(2, "Boot Manager", "bootmgfw.efi",
              "The Windows Boot Manager reads the Boot Configuration Data (BCD) "
              "store and presents/selects an OS entry.",
              ["\\EFI\\Microsoft\\Boot\\bootmgfw.efi", "BCD store"],
              "Tampering with BCD (bcdedit) can disable Secure Boot checks or "
              "enable test-signing to load unsigned malicious drivers."),
    BootStage(3, "Windows Loader", "winload.efi",
              "Loads the kernel, the HAL and boot-critical drivers into memory "
              "and validates their digital signatures.",
              ["winload.efi", "ntoskrnl.exe", "hal.dll"],
              "Driver Signature Enforcement (DSE) is enforced here; attackers "
              "abuse vulnerable signed drivers (BYOVD) to get kernel execution."),
    BootStage(4, "Kernel Initialization", "ntoskrnl.exe",
              "The kernel initialises the executive subsystems, memory manager "
              "and object manager, then starts the Session Manager.",
              ["ntoskrnl.exe", "Registry: SYSTEM hive"],
              "Rootkits hook kernel structures (SSDT, callbacks). ELAM drivers "
              "load early specifically to vet later boot-start drivers."),
    BootStage(5, "Session Manager", "smss.exe",
              "First user-mode process. Creates environment variables, page "
              "files and Session 0, then launches winlogon and csrss.",
              ["smss.exe", "csrss.exe", "wininit.exe"],
              "smss.exe should only ever be a child of System (PID 4). Any other "
              "parent is a strong process-masquerading indicator."),
    BootStage(6, "Logon", "winlogon.exe / lsass.exe",
              "winlogon presents the secure desktop; lsass validates credentials "
              "and issues access tokens. userinit launches the shell.",
              ["winlogon.exe", "lsass.exe", "userinit.exe", "explorer.exe"],
              "lsass holds credential material in memory - the prime target for "
              "credential dumping (Mimikatz). Credential Guard isolates it."),
]

LINUX_BOOT: List[BootStage] = [
    BootStage(1, "Power-On & POST", "UEFI/BIOS Firmware",
              "Firmware performs POST, initialises hardware and loads the first "
              "stage bootloader from the EFI system partition or MBR.",
              ["UEFI firmware", "/boot/efi"],
              "Same firmware-level threats as Windows; UEFI Secure Boot with "
              "shim + MOK controls what bootloaders may run."),
    BootStage(2, "Bootloader", "GRUB 2",
              "GRUB presents the boot menu, loads the kernel image and the "
              "initramfs into memory, and passes the kernel command line.",
              ["/boot/grub/grub.cfg", "/boot/vmlinuz-*"],
              "Editing the GRUB cmdline (init=/bin/bash) grants a root shell - "
              "why a GRUB password + full-disk encryption matter physically."),
    BootStage(3, "Kernel", "vmlinuz",
              "The kernel decompresses, detects hardware, mounts the initramfs "
              "as a temporary root, and initialises core subsystems.",
              ["/boot/vmlinuz-*", "dmesg / kernel ring buffer"],
              "Loadable kernel module (LKM) rootkits hijack syscalls. Signed "
              "modules + kernel lockdown mode reduce this attack surface."),
    BootStage(4, "initramfs", "initramfs / dracut",
              "A minimal in-memory root filesystem loads the drivers needed to "
              "find and mount the real root (e.g. LVM, LUKS decryption).",
              ["/boot/initramfs-*.img", "init script"],
              "Unlocking LUKS happens here; a malicious initramfs could capture "
              "the passphrase - hence measured boot / TPM binding."),
    BootStage(5, "init / systemd (PID 1)", "systemd",
              "The kernel starts PID 1. systemd mounts filesystems and brings the "
              "system up to the default target by starting units in dependency order.",
              ["/sbin/init -> systemd", "/etc/systemd/system/*", "default.target"],
              "systemd units and timers are a popular persistence mechanism; a "
              "rogue .service running as root re-launches malware on every boot."),
    BootStage(6, "User Session", "getty / Display Manager",
              "systemd reaches the graphical or multi-user target; getty or a "
              "display manager (gdm) presents login and starts the user session.",
              ["gdm / sshd / agetty", "/etc/pam.d/*", "PAM stack"],
              "Authentication runs through PAM; a malicious PAM module can log "
              "or bypass passwords. SSH keys and pam.d config are audit targets."),
]

BOOT_CHAINS: Dict[str, List[BootStage]] = {
    "windows": WINDOWS_BOOT,
    "linux": LINUX_BOOT,
}
