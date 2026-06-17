# ui/app_window.py
# QMainWindow chính: QStackedWidget, F11 fullscreen, close confirmation.

from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox
from PyQt6.QtGui     import QKeySequence, QShortcut
from PyQt6.QtCore    import Qt

from ui.controller       import SimulationController
from ui.menu_page        import MenuPage
from ui.simulation_page  import SimulationPage


_INDEX_MENU = 0
_INDEX_SIM  = 1


class AppWindow(QMainWindow):
    """QMainWindow ứng dụng chính."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "MULTI-AGENT EMERGENCY DISPATCH SYSTEM - HCM-UTE")
        self.resize(1280, 780)
        self.setMinimumSize(900, 600)

        self._ctrl = SimulationController(self)

        self._menu_page = MenuPage()
        self._sim_page  = SimulationPage(self._ctrl)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._menu_page)
        self._stack.addWidget(self._sim_page)
        self.setCentralWidget(self._stack)

        # Chuyển trang
        self._menu_page.sandbox_selected.connect(self._go_sandbox)
        self._menu_page.default_selected.connect(self._go_default)
        self._sim_page.go_to_menu.connect(self._go_menu)

        # F11 — fullscreen toggle (hoạt động ở bất kỳ trang nào)
        QShortcut(QKeySequence(Qt.Key.Key_F11), self).activated.connect(
            self._toggle_fullscreen)

        self._stack.setCurrentIndex(_INDEX_MENU)

    # ------------------------------------------------------------------ #
    #  Page transitions                                                    #
    # ------------------------------------------------------------------ #

    def _go_sandbox(self):
        self._ctrl.setup_sandbox_map()
        self._enter_simulation()

    def _go_default(self):
        self._ctrl.setup_default_map()
        self._enter_simulation()

    def _enter_simulation(self):
        self._sim_page.on_enter()
        self._stack.setCurrentIndex(_INDEX_SIM)

    def _go_menu(self):
        self._sim_page.on_leave()
        self._stack.setCurrentIndex(_INDEX_MENU)

    # ------------------------------------------------------------------ #
    #  Keyboard & window                                                   #
    # ------------------------------------------------------------------ #

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def closeEvent(self, event):
        """Hỏi xác nhận nếu simulation đang chạy và có agent/tai nạn chờ."""
        if (self._stack.currentIndex() == _INDEX_SIM and
                (self._ctrl.active_agents or self._ctrl.pending_accidents)):

            reply = QMessageBox.question(
                self,
                "Xác nhận thoát",
                "Simulation đang chạy.\nBạn có chắc muốn thoát không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

        self._ctrl.stop_timers()
        super().closeEvent(event)
