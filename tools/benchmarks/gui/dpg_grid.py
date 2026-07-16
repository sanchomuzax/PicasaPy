#!/usr/bin/env python3
"""Dear PyGui thumbnail-rács benchmark.

Megjegyzés: a DPG-ben nincs virtualizált lista — minden egyedi kép textúrába
kerül (a duplikátumok textúrát osztanak). Ez a DPG őszinte tesztje.
Használat: dpg_grid.py <thumbs_dir> [item_count]  ·  Esc = kilépés
"""
import sys
import time
from pathlib import Path

import dearpygui.dearpygui as dpg

CELL = 176


def main():
    thumbs = sorted(Path(sys.argv[1]).glob("*.jpg"))
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5000

    t0 = time.perf_counter()
    dpg.create_context()

    # egyedi textúrák betöltése (a raszter dekódot a DPG végzi)
    tex_ids = []
    with dpg.texture_registry():
        for p in thumbs:
            w, h, c, data = dpg.load_image(str(p))
            tex_ids.append(dpg.add_static_texture(width=w, height=h,
                                                  default_value=data))
    load_dt = time.perf_counter() - t0
    print(f"{len(tex_ids)} textúra betöltve: {load_dt:.2f}s", flush=True)

    cols = 7
    with dpg.window(tag="main", no_title_bar=True):
        fps_txt = dpg.add_text("- FPS")
        with dpg.child_window(autosize_x=True, autosize_y=True):
            with dpg.table(header_row=False, policy=dpg.mvTable_SizingFixedFit):
                for _ in range(cols):
                    dpg.add_table_column()
                for row in range(count // cols):
                    with dpg.table_row():
                        for col in range(cols):
                            idx = (row * cols + col) % len(tex_ids)
                            dpg.add_image(tex_ids[idx], width=CELL - 12,
                                          height=CELL - 44)

    def on_key(sender, key):
        if key == dpg.mvKey_Escape:
            dpg.stop_dearpygui()

    with dpg.handler_registry():
        dpg.add_key_press_handler(callback=on_key)

    dpg.create_viewport(title="PicasaPy bench: Dear PyGui",
                        width=1280, height=800)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("main", True)
    print(f"indulás→ablak: {time.perf_counter() - t0:.2f}s", flush=True)

    while dpg.is_dearpygui_running():
        dpg.set_value(fps_txt, f"{dpg.get_frame_rate():.0f} FPS")
        dpg.render_dearpygui_frame()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
