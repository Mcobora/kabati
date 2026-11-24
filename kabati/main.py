#!/usr/bin/env python3

#!/usr/bin/env python3

import os
import configparser
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Gio, GLib

CATEGORIES = {
    "All": ("applications-all", None),
    "Internet": ("web-browser", "Internet"),
    "Development": ("applications-development", "Development"),
    "Office": ("applications-office", "Office"),
    "Graphics": ("applications-graphics", "Graphics"),
    "Multimedia": ("applications-multimedia", "AudioVideo"),
    "Education": ("applications-education", "Education"),
    "Games": ("applications-games", "Game"),
    "System": ("applications-system", "System"),
    "Utilities": ("applications-utilities", "Utility"),
}

CSS = """
window#launcher-window {
    background-color: #181b2a;
    border: 1px solid rgba(255, 255, 255, 0.19);
    border-radius: 28px;
}

#main-panel {
    background-color: #181b2a;
    border-radius: 28px;
    padding: 30px;
}

#heading {
    color: #ffffff;
    font-size: 29px;
    font-weight: bold;
}

#subtitle {
    color: rgba(220, 225, 245, 0.58);
    font-size: 10px;
    letter-spacing: 2px;
}

entry#spotlight-search {
    background-color: rgba(255, 255, 255, 0.10);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.20);
    border-radius: 25px;
    padding: 15px 20px;
    font-size: 15px;
    caret-color: #89b4fa;
    box-shadow: none;
}

entry:focus {
    background-color: rgba(255, 255, 255, 0.14);
    border: 1px solid rgba(137, 180, 250, 0.65);
}

entry placeholder {
    color: rgba(220, 225, 245, 0.48);
}

scrolledwindow,
viewport,
flowbox {
    background-color: transparent;
    border: none;
}

.app-tile {
    background-color: rgba(255, 255, 255, 0.065);
    border: 1px solid rgba(255, 255, 255, 0.045);
    border-radius: 21px;
    padding: 16px;
    min-width: 120px;
    min-height: 130px;
    box-shadow: none;
    transition: background-color 180ms ease;
}

.app-tile:hover {
    background-color: rgba(255, 255, 255, 0.13);
    border: 1px solid rgba(255, 255, 255, 0.22);
}

.app-name {
    color: rgba(255, 255, 255, 0.92);
    font-size: 11px;
}

.category-bar {
    background-color: rgba(255, 255, 255, 0.105);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 20px;
    padding: 9px;
}

.category-button {
    background-color: transparent;
    color: rgba(230, 233, 247, 0.78);
    border: 1px solid transparent;
    border-radius: 14px;
    padding: 10px 9px;
    font-size: 11px;
    box-shadow: none;
}

.category-button:hover {
    background-color: rgba(255, 255, 255, 0.12);
    color: #ffffff;
}

.category-button.active-category {
    background-color: rgba(137, 180, 250, 0.20);
    color: #ffffff;
    border: 1px solid rgba(137, 180, 250, 0.35);
}

#close-button {
    background-color: rgba(255, 95, 86, 0.18);
    color: #ff7770;
    border-radius: 14px;
    border: 1px solid rgba(255, 95, 86, 0.25);
    padding: 7px 12px;
    box-shadow: none;
}

#close-button:hover {
    background-color: rgba(255, 95, 86, 0.32);
}
"""

def get_desktop_categories():
    paths = [
        "/usr/share/applications",
        "/usr/local/share/applications",
        os.path.expanduser("~/.local/share/applications")
    ]

    result = {}

    for base in paths:
        if not os.path.isdir(base):
            continue

        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d != "hidden"]

            for filename in files:
                if not filename.endswith(".desktop"):
                    continue

                path = os.path.join(root, filename)
                key = filename

                parser = configparser.ConfigParser(
                    interpolation=None,
                    strict=False
                )
                parser.optionxform = str

                try:
                    parser.read(path, encoding="utf-8")
                    cats = parser.get(
                        "Desktop Entry",
                        "Categories",
                        fallback=""
                    )
                    result[key] = set(cats.split(";"))
                except Exception:
                    result[key] = set()

    return result


class WesLauncher(Gtk.Window):

    def __init__(self):
        super().__init__(title="Kabati")
        self.set_icon_from_file(
            "/home/john/.local/share/icons/Kabati.svg"
        )

        self.set_name("launcher-window")
        self.set_decorated(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()

        if visual:
            self.set_visual(visual)

        self.set_app_paintable(True)

        geometry = screen.get_monitor_geometry(0)
        self.set_default_size(
            int(geometry.width * 0.85),
            int(geometry.height * 0.85)
        )

        self.selected_category = "All"
        self.apps = []

        self.load_css()
        self.build_interface()
        self.load_applications()

        self.connect("key-press-event", self.on_key_press)

    def load_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode())

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def build_interface(self):

        self.panel = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=17
        )
        self.panel.set_name("main-panel")
        self.add(self.panel)

        # Spotlight search at the top
        search_row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=0
        )
        search_row.set_halign(Gtk.Align.CENTER)

        self.search = Gtk.Entry()
        self.search.set_name("spotlight-search")
        self.search.set_size_request(520, -1)
        self.search.set_placeholder_text("Search Applications")
        self.search.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY,
            "system-search"
        )
        self.search.set_icon_activatable(
            Gtk.EntryIconPosition.PRIMARY, False
        )
        self.search.connect("changed", self.refresh_grid)

        search_row.pack_start(self.search, False, False, 0)
        self.panel.pack_start(search_row, False, False, 0)

        # Kabati heading
        header = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10
        )

        title_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=3
        )
        title_box.set_halign(Gtk.Align.CENTER)

        title = Gtk.Label(label="Kabati")
        title.set_name("heading")
        title.set_xalign(0.5)

        subtitle = Gtk.Label(label="APPLICATION LAUNCHER")
        subtitle.set_name("subtitle")
        subtitle.set_xalign(0.5)

        title_box.pack_start(title, False, False, 0)
        title_box.pack_start(subtitle, False, False, 0)

        close = Gtk.Button(label="✕")
        close.set_name("close-button")
        close.connect("clicked", lambda b: self.hide())

        header.pack_start(title_box, True, True, 0)
        header.pack_end(close, False, False, 0)

        self.panel.pack_start(header, False, False, 0)

        # Animated application grid
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(
            Gtk.StackTransitionType.SLIDE_LEFT_RIGHT
        )
        self.stack.set_transition_duration(300)

        self.flows = []

        for page in range(2):
            flow = Gtk.FlowBox()
            flow.set_selection_mode(Gtk.SelectionMode.NONE)
            flow.set_homogeneous(True)
            flow.set_max_children_per_line(5)
            flow.set_min_children_per_line(2)
            flow.set_row_spacing(20)
            flow.set_column_spacing(20)
            flow.set_filter_func(self.filter_application)

            scroll = Gtk.ScrolledWindow()
            scroll.set_policy(
                Gtk.PolicyType.NEVER,
                Gtk.PolicyType.AUTOMATIC
            )
            scroll.set_overlay_scrolling(False)
            scroll.add(flow)

            self.stack.add_named(scroll, f"page{page}")
            self.flows.append(flow)

        self.active_page = 0
        self.flow = self.flows[0]

        self.panel.pack_start(self.stack, True, True, 0)


        # Bottom category navigation
        category_frame = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL
        )
        category_frame.get_style_context().add_class("category-bar")

        for name, (icon_name, desktop_category) in CATEGORIES.items():

            button = Gtk.Button()
            button.set_relief(Gtk.ReliefStyle.NONE)
            button.get_style_context().add_class("category-button")

            content = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL,
                spacing=5
            )

            icon = Gtk.Image.new_from_icon_name(
                icon_name,
                Gtk.IconSize.MENU
            )

            label = Gtk.Label(label=name)

            content.pack_start(icon, False, False, 0)
            content.pack_start(label, False, False, 0)

            button.add(content)
            button.connect(
                "clicked",
                self.change_category,
                name
            )

            if name == "All":
                button.get_style_context().add_class(
                    "active-category"
                )

            category_frame.pack_start(
                button, True, True, 0
            )

        self.panel.pack_end(category_frame, False, False, 0)

    def load_applications(self):

        categories = get_desktop_categories()
        seen = set()

        for app in Gio.AppInfo.get_all():

            if not app.should_show():
                continue

            app_id = app.get_id()

            if not app_id or app_id in seen:
                continue

            seen.add(app_id)

            desktop_categories = categories.get(
                os.path.basename(app_id),
                set()
            )

            category = "Utilities"

            priority = [
                "Internet", "Development", "Office",
                "Graphics", "Multimedia", "Education",
                "Games", "System", "Utilities"
            ]

            for name in priority:
                desktop_key = CATEGORIES[name][1]
                if desktop_key in desktop_categories:
                    category = name
                    break

            self.apps.append({
                "app": app,
                "name": app.get_name(),
                "category": category,
                "icon": app.get_icon()
            })

        self.apps.sort(
            key=lambda x: x["name"].lower()
        )

        self.refresh_grid()

    def refresh_grid(self, *args, animate=False, direction=None):

        target_page = (
            1 - self.active_page if animate else self.active_page
        )
        target_flow = self.flows[target_page]

        for child in target_flow.get_children():
            target_flow.remove(child)

        query = self.search.get_text().lower()

        for item in self.apps:

            if query and query not in item["name"].lower():
                continue

            if (
                self.selected_category != "All"
                and item["category"] != self.selected_category
            ):
                continue

            button = Gtk.Button()
            button.set_relief(Gtk.ReliefStyle.NONE)
            button.get_style_context().add_class("app-tile")

            content = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL,
                spacing=9
            )

            image = Gtk.Image.new_from_gicon(
                item["icon"] or Gio.ThemedIcon.new(
                    "application-x-executable"
                ),
                Gtk.IconSize.DIALOG
            )
            image.set_pixel_size(80)

            label = Gtk.Label(label=item["name"])
            label.set_name("app-name")
            label.get_style_context().add_class("app-name")
            label.set_ellipsize(3)
            label.set_max_width_chars(17)

            content.pack_start(image, True, True, 0)
            content.pack_start(label, False, False, 0)

            button.add(content)
            button.connect(
                "clicked",
                self.launch_application,
                item["app"]
            )

            target_flow.add(button)

        target_flow.show_all()

        if animate:
            self.stack.set_transition_type(direction)
            self.stack.set_visible_child_name(
                f"page{target_page}"
            )

        self.active_page = target_page
        self.flow = target_flow

    def filter_application(self, child):
        return True

    def change_category(self, button, category):

        previous_category = self.selected_category
        self.selected_category = category

        for widget in button.get_parent().get_children():
            widget.get_style_context().remove_class(
                "active-category"
            )

        button.get_style_context().add_class(
            "active-category"
        )

        if category != previous_category:
            old_index = list(CATEGORIES).index(previous_category)
            new_index = list(CATEGORIES).index(category)

            direction = (
                Gtk.StackTransitionType.SLIDE_LEFT
                if new_index > old_index
                else Gtk.StackTransitionType.SLIDE_RIGHT
            )

            self.refresh_grid(
                animate=True,
                direction=direction
            )
        else:
            self.refresh_grid()

    def launch_application(self, button, app):

        try:
            app.launch([], None)
            self.hide()
        except Exception as error:
            print("Application launch failed:", error)

    def on_key_press(self, widget, event):

        if event.keyval == Gdk.KEY_Escape:
            self.hide()
            return True

        if event.keyval == Gdk.KEY_slash:
            self.search.grab_focus()
            return True

        return False


if __name__ == "__main__":

    import fcntl
    import signal
    import sys
    import os
    from gi.repository import GLib

    lock_path = "/tmp/wes-launcher.lock"
    pid_path = f"/tmp/wes-launcher-{os.getuid()}.pid"

    lock_file = open(lock_path, "a+")

    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        try:
            with open(pid_path) as f:
                existing_pid = int(f.read().strip())
            os.kill(existing_pid, signal.SIGUSR1)
        except (OSError, ValueError):
            pass
        sys.exit(0)

    launcher = WesLauncher()

    def toggle_launcher():
        if launcher.get_visible():
            launcher.hide()
        else:
            launcher.show_all()
            launcher.present()
            launcher.search.grab_focus()
        return False

    def handle_toggle(signum, frame):
        GLib.idle_add(toggle_launcher)

    signal.signal(signal.SIGUSR1, handle_toggle)

    with open(pid_path, "w") as f:
        f.write(str(os.getpid()))

    try:
        launcher.show_all()
        launcher.search.grab_focus()
        Gtk.main()
    finally:
        try:
            with open(pid_path) as f:
                if f.read().strip() == str(os.getpid()):
                    os.remove(pid_path)
        except FileNotFoundError:
            pass

        lock_file.close()
