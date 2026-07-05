"""Cinematic startup splash - the 'boot journey'.

BOOT LOGIC IS UNCHANGED: same 8 stages, same order, same messages, same timing,
same st.empty stepper and session gate. Only the visual frame is upgraded - each
stage pulses the relevant hardware and lights the OS-layer stack in sequence.
"""
import time
import streamlit as st
from core.config import AppConfig
from core.state import AppState

_P = AppConfig.PALETTE

HARDWARE = [
    ("PSU", "Power Supply", "\u26a1"),
    ("MB",  "Motherboard",  "\u25a6"),
    ("CPU", "CPU",          "\u2317"),
    ("RAM", "RAM",          "\u25a4"),
    ("SSD", "SSD",          "\u25a5"),
    ("GPU", "GPU",          "\u25eb"),
    ("NIC", "NIC",          "\u21c4"),
]

LAYERS = ["Hardware", "Firmware", "Boot Loader", "Kernel", "Drivers",
          "Core Processes", "Services", "Authentication", "Desktop"]


class BootScreen:
    # (label, message, progress%, active_hardware, layers_lit, current_layer)
    STAGES = [
        ("PWR",  "Pressing the power button...",        5,  ("PSU",),      1, 0),
        ("FW",   f"{AppConfig.APP_NAME} Firmware  -  v{AppConfig.VERSION}", 15, ("MB",), 2, 1),
        ("POST", "Hardware initialization (POST)...",   30, ("CPU", "MB"), 2, 0),
        ("MEM",  "Memory check - 32768 MB ... OK",      45, ("RAM",),      2, 1),
        ("UEFI", "Firmware initialization (UEFI)...",   60, ("MB", "SSD"), 3, 2),
        ("BOOT", "Loading boot components...",          75, ("SSD",),      5, 4),
        ("KRNL", "Starting operating system kernel...", 90, ("CPU", "RAM"),6, 5),
        ("GUI",  "Launching desktop...",               100, ("GPU", "NIC"),9, 8),
    ]

    def render(self) -> None:
        slot = st.empty()
        for label, message, pct, active_hw, lit, cur in self.STAGES:
            slot.markdown(self._frame(label, message, pct, active_hw, lit, cur),
                          unsafe_allow_html=True)
            time.sleep(0.7)
        time.sleep(0.3)
        AppState.set("system_booted", True)
        slot.empty()
        st.rerun()

    def _frame(self, label, message, pct, active_hw, lit, cur) -> str:
        hw_html = ""
        for key, name, icon in HARDWARE:
            cls = "ps-hw active" if key in active_hw else "ps-hw"
            hw_html += f'<div class="{cls}"><span class="ic">{icon}</span>{name}</div>'

        layer_html = ""
        for i, name in enumerate(LAYERS):
            if i == cur:
                cls = "ps-layer cur"
            elif i < lit:
                cls = "ps-layer on"
            else:
                cls = "ps-layer"
            layer_html += f'<div class="{cls}"><span class="dot"></span>{name}</div>'

        return f"""
        <div style="min-height:80vh;display:flex;flex-direction:column;
             align-items:center;justify-content:center;font-family:'Inter','Segoe UI',sans-serif;">

          <div style="display:flex;align-items:center;gap:.6rem;margin-bottom:1.3rem;">
            <div style="width:44px;height:44px;border-radius:12px;background:{_P.accent};
                 display:flex;align-items:center;justify-content:center;color:#fff;
                 font-size:1.2rem;font-weight:700;box-shadow:0 8px 24px rgba(59,130,246,.35);">&#9672;</div>
            <div style="text-align:left;">
              <div style="font-size:1.25rem;font-weight:700;color:{_P.text};">{AppConfig.APP_NAME}</div>
              <div style="letter-spacing:.16em;font-size:.66rem;color:{_P.text_muted};">BOOT SEQUENCE</div>
            </div>
          </div>

          <div style="display:flex;gap:1rem;width:760px;max-width:92vw;align-items:stretch;">
            <div class="ps-card" style="flex:1;margin-bottom:0;">
              <div class="ps-kv" style="margin-bottom:.6rem;">Hardware</div>
              <div class="ps-hwgrid">{hw_html}</div>
            </div>
            <div class="ps-card" style="flex:1;margin-bottom:0;">
              <div class="ps-kv" style="margin-bottom:.6rem;">Operating System Layers</div>
              {layer_html}
            </div>
          </div>

          <div style="width:760px;max-width:92vw;margin-top:1.1rem;">
            <div style="height:6px;background:{_P.border};border-radius:999px;overflow:hidden;">
              <div style="width:{pct}%;height:100%;
                   background:linear-gradient(90deg,{_P.accent},{_P.info});border-radius:999px;"></div>
            </div>
            <div style="margin-top:.7rem;color:{_P.text_muted};font-size:.85rem;letter-spacing:.02em;">
              <span style="font-weight:700;color:{_P.accent};">[{label}]</span> &nbsp;{message}
            </div>
          </div>

          <div style="margin-top:1.6rem;color:{_P.text_muted};font-size:.72rem;opacity:.6;">
            (c) {AppConfig.APP_NAME} - Educational OS Internals Platform
          </div>
        </div>
        """
