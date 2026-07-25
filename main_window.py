from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QStackedWidget, QStatusBar, QMenuBar, QDockWidget,
    QMessageBox, QApplication, QDialog, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QPixmap, QIcon
import os
from datetime import datetime

from database import DatabaseHandler
from styles import Styles, COLORS
from schedule_page import SchedulePage
from profile_page import ProfilePage
from export_page import ExportPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseHandler()
        self.init_ui()
        self.setup_menu_bar()
        self.setup_status_bar()
        self.setup_profile_dock()
        self.apply_styles()
        self.update_status_bar()
        
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.safe_update_status_bar)
        self.status_timer.start(60000) 
    
    def load_navigation_icon(self, icon_name, state="default"):
        icon_path = f"assets/icons/{icon_name}_{state}.png"
        
        if os.path.exists(icon_path):
            try:
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    return QIcon(scaled_pixmap)
            except Exception as e:
                print(f"Error loading icon {icon_path}: {e}")
        
        return None
    
    def setup_navigation_button(self, button, icon_name, text, default_emoji):
        default_icon = self.load_navigation_icon(icon_name, "default")
        clicked_icon = self.load_navigation_icon(icon_name, "clicked")
        
        if default_icon and clicked_icon:
            button.setIcon(default_icon)
            button.setText(f"  {text}") 
            button.setIconSize(button.size())
            
            button.default_icon = default_icon
            button.clicked_icon = clicked_icon
            button.has_custom_icons = True
        else:
            button.setText(f"{default_emoji} {text}")
            button.has_custom_icons = False
    
    def update_navigation_button_state(self, button, is_active):
        if hasattr(button, 'has_custom_icons') and button.has_custom_icons:
            if is_active and hasattr(button, 'clicked_icon'):
                button.setIcon(button.clicked_icon)
            elif hasattr(button, 'default_icon'):
                button.setIcon(button.default_icon)

        button.setChecked(is_active)
    
    def init_ui(self):
        self.setWindowTitle("Trackerin - To-Do Activity Tracker")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 600)
        
        icon_path = "assets/logo.png"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)  
        
        self.create_header(main_layout)
        
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        self.schedule_page = SchedulePage(self.db)
        self.export_page = ExportPage(self.db)
        self.profile_page = ProfilePage(self.db)
        
        self.profile_page.profile_updated.connect(self.refresh_header_profile)
        self.profile_page.profile_updated.connect(self.safe_update_status_bar)
        self.profile_page.set_main_window(self)
        
        self.stacked_widget.addWidget(self.schedule_page)
        self.stacked_widget.addWidget(self.export_page)
        self.stacked_widget.addWidget(self.profile_page)
        
        self.stacked_widget.setCurrentWidget(self.schedule_page)
        self.update_navigation_states()
    
    def create_header(self, main_layout):
        header_widget = QWidget()
        header_widget.setObjectName("headerWidget")
        header_widget.setFixedHeight(80)
        
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        left_section = QHBoxLayout()
        
        logo_icon = QLabel()
        logo_icon.setFixedSize(50, 50)
        icon_path = "assets/logo.png"
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            scaled_pixmap = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_icon.setPixmap(scaled_pixmap)
        else:
            logo_icon.setText("📋")
            logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_icon.setStyleSheet("font-size: 32px;")
        
        left_section.addWidget(logo_icon)
        left_section.addSpacing(20)
        
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(5)
        
        self.schedule_button = QPushButton()
        self.schedule_button.setObjectName("navButton")
        self.schedule_button.setCheckable(True)
        self.schedule_button.clicked.connect(self.show_schedule_page)
        self.setup_navigation_button(self.schedule_button, "schedule", "Schedule", "📅")
        
        self.export_button = QPushButton()
        self.export_button.setObjectName("navButton")
        self.export_button.setCheckable(True)
        self.export_button.clicked.connect(self.show_export_page)
        self.setup_navigation_button(self.export_button, "export", "Export", "📊")
        
        self.profile_button = QPushButton()
        self.profile_button.setObjectName("navButton")
        self.profile_button.setCheckable(True)
        self.profile_button.clicked.connect(self.show_profile_page)
        self.setup_navigation_button(self.profile_button, "profile", "Profile", "👤")
        
        nav_layout.addWidget(self.schedule_button)
        nav_layout.addWidget(self.export_button)
        nav_layout.addWidget(self.profile_button)
        
        left_section.addLayout(nav_layout)
        header_layout.addLayout(left_section)
        
        header_layout.addStretch()
        
        user_info_layout = QHBoxLayout()
        
        self.header_profile_pic = QLabel()
        self.header_profile_pic.setFixedSize(40, 40)
        self.header_profile_pic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_profile_pic.setObjectName("profilePic")
        
        self.load_header_profile_picture()
        
        profile_data = self.safe_get_user_profile()
        user_name = profile_data['fullname'] if profile_data else "Demo User"
        user_status = profile_data['status_type'] if profile_data else "User"
        self.user_label = QLabel(f"{user_name}\n{user_status}")
        self.user_label.setObjectName("userLabel")
        
        user_info_layout.addWidget(self.header_profile_pic)
        user_info_layout.addWidget(self.user_label)
        
        header_layout.addLayout(user_info_layout)
        
        main_layout.addWidget(header_widget)
    
    def safe_get_user_profile(self):
        """Safely get user profile with error handling"""
        try:
            return self.db.get_user_profile()
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None

    @staticmethod
    def format_profile_status(profile_data, current_time=None):
        """Build a status label without exposing hard-coded personal data."""
        profile = profile_data or {
            "fullname": "Demo User",
            "status_type": "User",
            "student_id": "",
        }
        parts = [f"{profile['status_type']}: {profile['fullname']}"]
        if profile.get("student_id"):
            parts.append(f"ID: {profile['student_id']}")
        if current_time:
            parts.append(current_time)
        return " | ".join(parts)
    
    def load_header_profile_picture(self):
        try:
            profile_data = self.safe_get_user_profile()
            
            if profile_data and profile_data.get('profile_picture') and os.path.exists(profile_data['profile_picture']):
                try:
                    pixmap = QPixmap(profile_data['profile_picture'])
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                        
                        circular_pixmap = QPixmap(40, 40)
                        circular_pixmap.fill(Qt.GlobalColor.transparent)
                        
                        from PyQt6.QtGui import QPainter, QPen, QBrush
                        painter = QPainter(circular_pixmap)
                        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                        painter.setBrush(QBrush(scaled_pixmap))
                        painter.setPen(QPen(Qt.GlobalColor.transparent))
                        painter.drawEllipse(0, 0, 40, 40)
                        painter.end()
                        
                        self.header_profile_pic.setPixmap(circular_pixmap)
                        self.header_profile_pic.setText("")
                        return
                except Exception as e:
                    print(f"Error loading header profile picture: {e}")
        except Exception as e:
            print(f"Error in load_header_profile_picture: {e}")
        
        self.header_profile_pic.setText("👤")
        self.header_profile_pic.setStyleSheet("""
            QLabel {
                background-color: #0E2C75;
                color: #ffffff;
                border-radius: 20px;
                font-size: 20px;
            }
        """)
    
    def update_navigation_states(self):
        current_page = self.stacked_widget.currentWidget()
        
        self.update_navigation_button_state(self.schedule_button, False)
        self.update_navigation_button_state(self.export_button, False)
        self.update_navigation_button_state(self.profile_button, False)
        
        if current_page == self.schedule_page:
            self.update_navigation_button_state(self.schedule_button, True)
        elif current_page == self.export_page:
            self.update_navigation_button_state(self.export_button, True)
        elif current_page == self.profile_page:
            self.update_navigation_button_state(self.profile_button, True)
    
    def setup_menu_bar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu('File')
        new_task_action = QAction('New Task', self)
        new_task_action.setShortcut('Ctrl+N')
        new_task_action.triggered.connect(self.new_task_shortcut)
        file_menu.addAction(new_task_action)

        file_menu.addSeparator()
    
        export_action = QAction('Export to CSV', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.show_export_page)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        edit_menu = menubar.addMenu('Edit')
        
        paste_action = QAction('Paste from Clipboard', self)
        paste_action.setShortcut('Ctrl+V')
        paste_action.triggered.connect(self.paste_from_clipboard)
        edit_menu.addAction(paste_action)
        
        view_menu = menubar.addMenu('View')
        
        toggle_profile_dock = QAction('Toggle Profile Dock', self)
        toggle_profile_dock.triggered.connect(self.toggle_profile_dock)
        view_menu.addAction(toggle_profile_dock)
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('Application Info', self)
        about_action.setShortcut('F1')
        about_action.triggered.connect(self.show_modern_about)
        help_menu.addAction(about_action)
        
        help_menu.addSeparator()
        
        user_guide_action = QAction('User Guide', self)
        user_guide_action.triggered.connect(self.show_user_guide)
        help_menu.addAction(user_guide_action)
    
    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_bar.setStyleSheet(Styles.STATUS_BAR_STYLE)
        self.status_bar.setFixedHeight(25) 
        
        try:
            profile_data = self.safe_get_user_profile()
            status_text = self.format_profile_status(profile_data)
        except Exception as e:
            print(f"Error in setup_status_bar: {e}")
            status_text = self.format_profile_status(None)
        
        left_status_label = QLabel(status_text)
        left_status_label.setStyleSheet(Styles.STUDENT_INFO_STATUS_STYLE)
        self.status_bar.addWidget(left_status_label)
        
        copyright_label = QLabel("2025 @ Trackerin. Copyrights")
        copyright_label.setStyleSheet(Styles.STUDENT_INFO_STATUS_STYLE)
        self.status_bar.addPermanentWidget(copyright_label)
        
        self.status_bar.showMessage("")
    
    def setup_profile_dock(self):
        self.profile_dock = QDockWidget("Profile Management", self)
        self.profile_dock.setObjectName("profileDock")
        dock_content = self.profile_page.get_profile_dock_content()
        
        self.profile_dock.setWidget(dock_content)
        self.profile_dock.setStyleSheet(Styles.DOCK_WIDGET_STYLE)
        
        self.profile_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | 
            Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.profile_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable | 
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable 
        )
        
        self.profile_dock.setMinimumWidth(280)
        self.profile_dock.setMaximumWidth(350)
        
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.profile_dock)
        
        if hasattr(self, 'profile_dock_action'):
            self.profile_dock_action.triggered.connect(self.toggle_profile_dock)
            self.profile_dock.visibilityChanged.connect(self.profile_dock_action.setChecked)
        
        self.profile_dock.hide()
    
    def show_schedule_page(self):
        self.stacked_widget.setCurrentWidget(self.schedule_page)
        self.update_navigation_states()
        self.schedule_page.refresh_current_view()
        self.profile_dock.hide()
    
    def show_export_page(self):
        self.stacked_widget.setCurrentWidget(self.export_page)
        self.update_navigation_states()
        self.export_page.refresh_data()
        self.profile_dock.hide()
    
    def show_profile_page(self):
        self.stacked_widget.setCurrentWidget(self.profile_page)
        self.update_navigation_states()
        self.profile_page.refresh_table()
        self.profile_dock.show()
    
    def toggle_profile_dock(self):
        if self.profile_dock.isVisible():
            self.profile_dock.hide()
        else:
            self.profile_dock.show()
    
    def new_task_shortcut(self):
        self.show_schedule_page()
        self.schedule_page.focus_task_input()
    
    def paste_from_clipboard(self):
        try:
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            
            if text:
                current_page = self.stacked_widget.currentWidget()
                if hasattr(current_page, 'paste_to_active_input'):
                    current_page.paste_to_active_input(text)
                else:
                    reply = QMessageBox.question(self, "Paste Clipboard", 
                                               f"Clipboard content:\n{text}\n\nWould you like to paste this to the current page?",
                                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.Yes:
                        if hasattr(current_page, 'paste_to_active_input'):
                            current_page.paste_to_active_input(text)
        except Exception as e:
            print(f"Error in paste_from_clipboard: {e}")
            QMessageBox.warning(self, "Error", "Failed to access clipboard.")
    
    def show_about(self):
        QMessageBox.about(self, "About Trackerin", 
                         "Trackerin - To-Do Activity Tracker\n\n"
                         "A modern task management application built with PyQt6.\n\n"
                         "Features:\n"
                         "• Task scheduling and management\n"
                         "• Calendar integration\n"
                         "• Activity history tracking\n"
                         "• CSV export functionality\n"
                         "• User profile management\n"
                         "• Custom navigation icons\n"
                         "• Profile picture support\n"
                         "• Clipboard paste support\n\n"
                         "Version 1.1\n"
                         "© 2024 Trackerin Inc.")
    
    def show_modern_about(self):        
        dialog = QDialog(self)
        dialog.setWindowTitle("Application Information")
        dialog.setFixedSize(500, 650) 
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #f8f9fa, stop:1 #e9ecef);
                border-radius: 15px;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)  
        
        header_layout = QHBoxLayout()
        
        icon_label = QLabel()
        icon_label.setFixedSize(80, 80)
        if os.path.exists("assets/logo.png"):
            pixmap = QPixmap("assets/logo.png")
            scaled_pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(scaled_pixmap)
        else:
            icon_label.setText("📋")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("font-size: 48px; background-color: #0E2C75; border-radius: 15px; color: white;")
        
        title_layout = QVBoxLayout()
        title_label = QLabel("Trackerin")
        title_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #2c3e50; margin: 0;")
        
        subtitle_label = QLabel("To-Do Activity Tracker")
        subtitle_label.setStyleSheet("font-size: 16px; color: #6c757d; margin: 0;")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        title_layout.addStretch()
        
        header_layout.addWidget(icon_label)
        header_layout.addSpacing(20)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("border: 1px solid #dee2e6; margin: 10px 0;")
        layout.addWidget(separator)
        
        desc_label = QLabel("A modern task management application built with PyQt6 for efficient productivity tracking.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 14px; color: #495057; line-height: 1.5; margin-bottom: 20px;")
        layout.addWidget(desc_label)
        
        features_title = QLabel("✨ Key Features")
        features_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(features_title)
        
        features_text = """📅 Task scheduling and management
🗓️ Calendar integration
📊 Activity history tracking
💾 CSV export functionality
👤 User profile management
🎨 Custom navigation icons
🖼️ Profile picture support
📋 Clipboard paste support"""
        
        features_label = QLabel(features_text)
        features_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 10px;
                padding: 25px;
                margin: 5px 0px;
                font-size: 14px;
                color: #495057;
                line-height: 1.8;
            }
        """)
        features_label.setWordWrap(True)
        features_label.setMinimumHeight(200) 
        features_label.setContentsMargins(5, 5, 5, 5) 
        layout.addWidget(features_label)
        
        version_layout = QHBoxLayout()
        
        version_label = QLabel("Version 1.1")
        version_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #0E2C75;")
        
        copyright_label = QLabel("© 2025 Trackerin Inc.")
        copyright_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        
        version_layout.addWidget(version_label)
        version_layout.addStretch()
        version_layout.addWidget(copyright_label)
        
        layout.addLayout(version_layout)
        
        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #0E2C75;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        close_button.clicked.connect(dialog.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def show_user_guide(self):
        QMessageBox.information(self, "User Guide", 
                               "📖 Trackerin User Guide\n\n"
                               "🔹 Schedule Page: Add and manage your daily tasks\n"
                               "🔹 Export Page: Export your data to CSV format\n"
                               "🔹 Profile Page: View activity history and manage profile\n\n"
                               "⌨️ Keyboard Shortcuts:\n"
                               "• Ctrl+N: New Task\n"
                               "• Ctrl+E: Export Data\n"
                               "• Ctrl+V: Paste from Clipboard\n"
                               "• F1: Application Info\n\n"
                               "💡 Tips:\n"
                               "• Double-click table items to edit\n"
                               "• Use the calendar to navigate dates\n"
                               "• Upload custom navigation icons to assets/icons/\n"
                               "• Change profile picture in Profile dock")
    
    def refresh_header_profile(self):
        try:
            profile_data = self.safe_get_user_profile()
            user_name = profile_data['fullname'] if profile_data else "Demo User"
            user_status = profile_data['status_type'] if profile_data else "User"
            
            self.user_label.setText(f"{user_name}\n{user_status}")
            
            self.load_header_profile_picture()
        except Exception as e:
            print(f"Error refreshing header profile: {e}")
    
    def safe_update_status_bar(self):
        """Safely update status bar with comprehensive error handling"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            profile_data = self.safe_get_user_profile()
            
            status_text = self.format_profile_status(profile_data, current_time)
            
            for widget in self.status_bar.children():
                if isinstance(widget, QLabel) and not widget.text().startswith("2025"):
                    widget.setText(status_text)
                    break
                    
        except Exception as e:
            print(f"Error updating status bar: {e}")
            try:
                for widget in self.status_bar.children():
                    if isinstance(widget, QLabel) and not widget.text().startswith("2025"):
                        widget.setText(self.format_profile_status(None))
                        break
            except Exception as fallback_error:
                print(f"Fallback status bar update failed: {fallback_error}")
    
    def update_status_bar(self):
        self.safe_update_status_bar()
    
    def apply_styles(self):
        enhanced_nav_button_style = """
            QPushButton#navButton {
                background-color: transparent;
                border: none;
                color: #6c757d;
                font-size: 16px;
                font-weight: 500;
                padding: 12px 20px;
                margin: 5px;
                border-radius: 8px;
                min-width: 100px;
                text-align: left;
            }
            
            QPushButton#navButton:hover {
                background-color: #f8f9fa;
                color: #2c3e50;
            }
            
            QPushButton#navButton:checked {
                background-color: #0E2C75;
                color: #ffffff;
            }
            
            QPushButton#navButton:pressed {
                background-color: #0056b3;
                color: #ffffff;
            }
        """
        
        self.setStyleSheet(
            Styles.MAIN_WINDOW_STYLE + 
            Styles.GENERAL_WIDGET_STYLE + 
            Styles.HEADER_STYLE +
            enhanced_nav_button_style +
            Styles.TAB_WIDGET_STYLE
        )
    
    def closeEvent(self, event):
        try:
            reply = QMessageBox.question(self, 'Exit Application',
                                       'Are you sure you want to exit?',
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                       QMessageBox.StandardButton.Yes)
            
            if reply == QMessageBox.StandardButton.Yes:
                if hasattr(self, 'status_timer'):
                    self.status_timer.stop()
                event.accept()
            else:
                event.ignore()
        except Exception as e:
            print(f"Error in closeEvent: {e}")
            event.accept()  
