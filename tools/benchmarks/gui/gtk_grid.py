#!/usr/bin/env python3
"""GTK4 (PyGObject) thumbnail-rács benchmark — virtualizált Gtk.GridView.

Rendszer-Pythonnal futtatandó (python3-gi). Esc = kilépés.
Használat: gtk_grid.py <thumbs_dir> [item_count]
"""
import sys
import time
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GLib, GObject, Gtk  # noqa: E402

T0 = time.perf_counter()


class ThumbItem(GObject.Object):
    def __init__(self, path):
        super().__init__()
        self.path = path


class App(Gtk.Application):
    def __init__(self, paths):
        super().__init__(application_id="hu.picasapy.gtkbench")
        self.paths = paths
        self.frames = 0
        self.texture_cache = {}

    def do_activate(self):
        win = Gtk.ApplicationWindow(application=self, title="PicasaPy bench: GTK4 GridView")
        win.set_default_size(1280, 800)

        store = Gtk.StringList.new([str(p) for p in self.paths])
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self.on_setup)
        factory.connect("bind", self.on_bind)
        grid = Gtk.GridView(model=Gtk.NoSelection(model=store), factory=factory)
        grid.set_min_columns(4)
        grid.set_max_columns(12)

        scroller = Gtk.ScrolledWindow()
        scroller.set_child(grid)

        self.fps_label = Gtk.Label(label="- FPS")
        self.fps_label.add_css_class("title-3")
        overlay = Gtk.Overlay()
        overlay.set_child(scroller)
        self.fps_label.set_halign(Gtk.Align.START)
        self.fps_label.set_valign(Gtk.Align.START)
        self.fps_label.set_margin_start(8)
        self.fps_label.set_margin_top(8)
        overlay.add_overlay(self.fps_label)

        win.set_child(overlay)

        key = Gtk.EventControllerKey()
        key.connect("key-pressed", self.on_key)
        win.add_controller(key)

        win.add_tick_callback(self.on_tick)
        GLib.timeout_add(1000, self.on_second)

        win.present()
        print(f"indulás→ablak: {time.perf_counter() - T0:.2f}s", flush=True)

    def on_setup(self, factory, item):
        pic = Gtk.Picture()
        pic.set_size_request(176, 176)
        pic.set_content_fit(Gtk.ContentFit.CONTAIN)
        item.set_child(pic)

    def on_bind(self, factory, item):
        path = item.get_item().get_string()
        tex = self.texture_cache.get(path)
        if tex is None:
            tex = Gdk.Texture.new_from_filename(path)
            self.texture_cache[path] = tex
        item.get_child().set_paintable(tex)

    def on_tick(self, widget, clock):
        self.frames += 1
        return GLib.SOURCE_CONTINUE

    def on_second(self):
        self.fps_label.set_label(f"{self.frames} FPS")
        self.frames = 0
        return GLib.SOURCE_CONTINUE

    def on_key(self, ctrl, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.quit()
        return False


def main():
    thumbs = sorted(Path(sys.argv[1]).glob("*.jpg"))
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    paths = [thumbs[i % len(thumbs)] for i in range(count)]
    app = App(paths)
    app.run(None)


if __name__ == "__main__":
    main()
