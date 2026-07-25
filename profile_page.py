import csv
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTableWidget, QTableWidgetItem, QLineEdit, QMessageBox,
    QHeaderView, QComboBox, QFileDialog, QDockWidget,
    QInputDialog, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPixmap
from database import DatabaseHandler
from styles import Styles, COLORS

class ProfilePage(QWidget):
    profile_updated = pyqtSignal()
    def __init__(self, db: DatabaseHandler):
        super().__init__()
        self.db = db
        self.current_tasks = []
        self.main_window = None  
        self.profile_pic_frame = None  
        self.init_ui()
        self.create_profile_dock()
        self.load_data()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)  
        main_layout.setSpacing(10) 
        
        self.create_activity_history(main_layout)
    
    def create_activity_history(self, parent_layout):
        title_label = QLabel("Activity History")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 20px;
            }
        """)
        parent_layout.addWidget(title_label)
        
        search_layout = QHBoxLayout()
        
        filter_button = QPushButton("🔽 Filter")
        filter_button.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 16px;
                color: #2c3e50;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        filter_button.clicked.connect(self.show_filter_options)
        
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchBox")
        self.search_input.setPlaceholderText("Search Users by Name, Email or Date (Ctrl+V to paste)")
        self.search_input.textChanged.connect(self.search_tasks)
        self.search_input.setStyleSheet(Styles.SEARCH_INPUT_STYLE)
        
        search_layout.addWidget(filter_button)
        search_layout.addWidget(self.search_input)
        parent_layout.addLayout(search_layout)
        
        self.create_activity_table(parent_layout)
    
    def create_activity_table(self, parent_layout):
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(7)
        
        headers = ["Date", "Activity", "Start Time", "End Time", "Duration", "Status", "Actions"]
        self.activity_table.setHorizontalHeaderLabels(headers)
        self.activity_table.verticalHeader().setVisible(False)
        
        self.activity_table.verticalHeader().setDefaultSectionSize(40)  
        
        header = self.activity_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # Activity
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Start Time
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # End Time
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Duration
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)             # Actions 
        header.resizeSection(6, 80) 
        
        self.activity_table.setSortingEnabled(True)
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Enable double-click editing with specific column handling
        self.activity_table.itemDoubleClicked.connect(self.edit_task_column)
        
        self.activity_table.setStyleSheet(Styles.TABLE_STYLE)
        
        parent_layout.addWidget(self.activity_table)
        
        self.pagination_label = QLabel("1-10 of 276")
        self.pagination_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pagination_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        parent_layout.addWidget(self.pagination_label)
    
    def create_profile_dock(self):
        pass
    
    def load_profile_image(self, image_path):
        if not image_path or not os.path.exists(image_path):
            return "👤"
        
        try:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                return "👤" 
            
            scaled_pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            
            circular_pixmap = QPixmap(100, 100)
            circular_pixmap.fill(Qt.GlobalColor.transparent)
            
            from PyQt6.QtGui import QPainter, QPen, QBrush
            painter = QPainter(circular_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QBrush(scaled_pixmap))
            painter.setPen(QPen(Qt.GlobalColor.transparent))
            painter.drawEllipse(0, 0, 100, 100)
            painter.end()
            
            return circular_pixmap
        except Exception as e:
            print(f"Error loading profile image: {e}")
            return "👤"
    
    def get_profile_dock_content(self):
        dock_widget = QWidget()
        dock_layout = QVBoxLayout(dock_widget)
        dock_layout.setContentsMargins(15, 15, 15, 15)
        dock_layout.setSpacing(15)
        
        profile_view_label = QLabel("Profile View")
        profile_view_label.setStyleSheet(Styles.DOCK_TITLE_STYLE)
        dock_layout.addWidget(profile_view_label)
        
        self.profile_pic_frame = QLabel()
        self.profile_pic_frame.setFixedSize(100, 100)
        self.profile_pic_frame.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.profile_pic_frame.setStyleSheet("""
            QLabel {
                background-color: #495057;
                border-radius: 50px;
                border: 2px solid #dee2e6;
                color: white;
                font-size: 48px;
            }
        """)
        
        profile_data = self.db.get_user_profile()
        if profile_data and profile_data.get('profile_picture'):
            profile_image = self.load_profile_image(profile_data['profile_picture'])
            if isinstance(profile_image, QPixmap):
                self.profile_pic_frame.setPixmap(profile_image)
                self.profile_pic_frame.setText("") 
            else:
                self.profile_pic_frame.setText(profile_image)
        else:
            self.profile_pic_frame.setText("👤")
        
        pic_layout = QHBoxLayout()
        pic_layout.addStretch()
        pic_layout.addWidget(self.profile_pic_frame)
        pic_layout.addStretch()
        dock_layout.addLayout(pic_layout)
        
        if profile_data:
            name_label = QLabel(profile_data['fullname'])
        else:
            name_label = QLabel("Demo User")
        
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                margin: 10px 0;
            }
        """)
        dock_layout.addWidget(name_label)
        
        change_profile_btn = QPushButton("Change Profile")
        change_profile_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 16px;
                color: #2c3e50;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        change_profile_btn.clicked.connect(self.change_profile_picture)
        dock_layout.addWidget(change_profile_btn)
        
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #dee2e6; margin: 10px 0;")
        dock_layout.addWidget(separator)
        
        profile_form_label = QLabel("Set My Profile")
        profile_form_label.setStyleSheet(Styles.DOCK_TITLE_STYLE)
        dock_layout.addWidget(profile_form_label)
        
        profile_data = self.db.get_user_profile()
        
        name_layout = QVBoxLayout()
        name_label = QLabel("Fullname")
        name_label.setStyleSheet("color: #2c3e50; font-size: 12px; font-weight: 500;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your full name (Ctrl+V to paste)")
        self.name_input.setStyleSheet(Styles.LINE_EDIT_STYLE)
        if profile_data:
            self.name_input.setText(profile_data['fullname'])
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        dock_layout.addLayout(name_layout)
        
        email_layout = QVBoxLayout()
        email_label = QLabel("Email")
        email_label.setStyleSheet("color: #2c3e50; font-size: 12px; font-weight: 500;")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email (Ctrl+V to paste)")
        self.email_input.setStyleSheet(Styles.LINE_EDIT_STYLE)
        if profile_data:
            self.email_input.setText(profile_data['email'])
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_input)
        dock_layout.addLayout(email_layout)
        
        id_layout = QVBoxLayout()
        id_label = QLabel("Student ID")
        id_label.setStyleSheet("color: #2c3e50; font-size: 12px; font-weight: 500;")
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Enter your student ID (Ctrl+V to paste)")
        self.id_input.setStyleSheet(Styles.LINE_EDIT_STYLE)
        if profile_data:
            self.id_input.setText(profile_data['student_id'])
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.id_input)
        dock_layout.addLayout(id_layout)
        
        status_layout = QVBoxLayout()
        status_label = QLabel("Type Of Status")
        status_label.setStyleSheet("color: #2c3e50; font-size: 12px; font-weight: 500;")
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Student", "Teacher", "Staff", "Other"])
        
        self.status_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #ffffff;
                font-size: 14px;
                min-height: 20px;
                padding-right: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #6c757d; 
                width: 0px;
                height: 0px;
            }
            QComboBox::down-arrow:hover {
                border-top-color: #495057;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #dee2e6;
                background-color: #ffffff;
                selection-background-color: #0E2C75;
                selection-color: #ffffff;
            }
        """)
        
        if profile_data:
            index = self.status_combo.findText(profile_data['status_type'])
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_combo)
        dock_layout.addLayout(status_layout)
        
        submit_button = QPushButton("Submit")
        submit_button.setStyleSheet("""
            QPushButton {
                background-color: #0E2C75;
                color: #ffffff;
                border: 2px solid #0E2C75;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 500;
                min-width: 120px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #0056b3;
                border-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
                border-color: #004085;
            }
        """)
        submit_button.clicked.connect(self.update_profile)
        dock_layout.addWidget(submit_button)
        dock_layout.addStretch(1)
        
        return dock_widget
    
    def set_main_window(self, main_window):
        self.main_window = main_window
    
    def load_data(self):
        try:
            self.current_tasks = self.db.get_all_tasks()
            if self.current_tasks is None:
                self.current_tasks = []
            self.populate_table(self.current_tasks)
        except Exception as e:
            print(f"Error loading profile data: {e}")
            self.current_tasks = []
            self.populate_table([])
    
    def populate_table(self, tasks):
        if not tasks:
            tasks = []
            
        self.activity_table.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            try:
                # Date
                date_item = QTableWidgetItem(str(task.get('start_date', 'N/A')))
                self.activity_table.setItem(row, 0, date_item)
                
                # Activity
                activity_item = QTableWidgetItem(str(task.get('title', 'N/A')))
                self.activity_table.setItem(row, 1, activity_item)
                
                # Start Time
                start_time = QTableWidgetItem(str(task.get('start_time', 'N/A')))
                self.activity_table.setItem(row, 2, start_time)
                
                # End Time
                end_time = QTableWidgetItem(str(task.get('end_time', 'N/A')))
                self.activity_table.setItem(row, 3, end_time)
                
                # Duration (calculated)
                duration = self.calculate_duration(
                    task.get('start_time', '00:00:00'), 
                    task.get('end_time', '00:00:00')
                )
                duration_item = QTableWidgetItem(duration)
                self.activity_table.setItem(row, 4, duration_item)
                
                # Status
                status_text = task.get('status', 'Not Yet')
                status_item = QTableWidgetItem(status_text)
                if status_text == 'Finished':
                    status_item.setBackground(QColor(212, 237, 218))  # Light green
                else:
                    status_item.setBackground(QColor(248, 215, 218))  # Light pink
                self.activity_table.setItem(row, 5, status_item)
                
                delete_btn = QPushButton("Delete")
                delete_btn.setToolTip("Delete this task")
                delete_btn.setFixedSize(55, 20) 
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        border: none;
                        border-radius: 4px;
                        color: #ffffff;
                        font-size: 8px;
                        font-weight: bold;
                        text-align: center;
                        margin: 1px;
                    }
                    QPushButton:hover { 
                        background-color: #c82333; 
                    }
                    QPushButton:pressed { 
                        background-color: #bd2130; 
                    }
                """)
                delete_btn.clicked.connect(lambda checked, task_id=task.get('id'): self.delete_task(task_id))
                
                button_widget = QWidget()
                button_layout = QHBoxLayout(button_widget)
                button_layout.setContentsMargins(0, 0, 0, 0)
                button_layout.addWidget(delete_btn)
                
                button_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
                self.activity_table.setCellWidget(row, 6, button_widget)
                
            except Exception as e:
                print(f"Error populating row {row}: {e}")
                for col in range(6):
                    if not self.activity_table.item(row, col):
                        self.activity_table.setItem(row, col, QTableWidgetItem("Error"))
        
        total_tasks = len(tasks)
        if total_tasks > 0:
            self.pagination_label.setText(f"1-{min(total_tasks, 10)} of {total_tasks}")
        else:
            self.pagination_label.setText("No activities found")
    
    def calculate_duration(self, start_time, end_time):
        try:
            start = datetime.strptime(start_time, "%H:%M:%S")
            end = datetime.strptime(end_time, "%H:%M:%S")
            
            if end < start:
                end = end.replace(day=start.day + 1)
            
            duration = end - start
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            
            return f"{hours}h {minutes}m"
        except:
            return "N/A"
    
    def search_tasks(self, text):
        try:
            query_text = text.strip()
            if not query_text:
                filtered_tasks = self.db.get_all_tasks()
            else:
                filtered_tasks = self.db.search_tasks(query_text)
            
            if filtered_tasks is None:
                filtered_tasks = []
                
            self.populate_table(filtered_tasks)
        except Exception as e:
            print(f"Error searching tasks: {e}")
            self.populate_table([])
    
    def edit_task_column(self, item):
        row = item.row()
        column = item.column()
        
        task_id = None
        for i, task in enumerate(self.current_tasks):
            if i == row:
                task_id = task.get('id')
                break
        
        if task_id is None:
            return
        
        current_task = next((task for task in self.current_tasks if task.get('id') == task_id), None)
        if not current_task:
            return
        
        headers = ["Date", "Activity", "Start Time", "End Time", "Duration", "Status", "Actions"]
        column_name = headers[column]
        
        if column == 0:  # Date
            QMessageBox.information(self, "Edit Date", "Date editing is not allowed for consistency.")
            return
        elif column == 1:  # Activity
            new_value, ok = QInputDialog.getText(
                self, f'Edit {column_name}',
                f'Enter new activity title:',
                text=current_task.get('title', '')
            )
            if ok and new_value.strip():
                if self.db.update_task(task_id, new_value, new_value, 
                                     current_task.get('start_date'), current_task.get('end_date'),
                                     current_task.get('start_time'), current_task.get('end_time')):
                    QMessageBox.information(self, "Success", "Activity updated successfully!")
                    self.refresh_table()
                else:
                    QMessageBox.warning(self, "Error", "Failed to update activity.")
        elif column == 2:  # Start Time
            new_value, ok = QInputDialog.getText(
                self, f'Edit {column_name}',
                f'Enter new start time (HH:MM:SS):',
                text=current_task.get('start_time', '')
            )
            if ok and new_value.strip():
                try:
                    from datetime import datetime
                    datetime.strptime(new_value, '%H:%M:%S')
                    # Update in database
                    if self.db.update_task(task_id, current_task.get('title'), current_task.get('description'),
                                         current_task.get('start_date'), current_task.get('end_date'),
                                         new_value, current_task.get('end_time')):
                        QMessageBox.information(self, "Success", "Start time updated successfully!")
                        self.refresh_table()
                    else:
                        QMessageBox.warning(self, "Error", "Failed to update start time.")
                except ValueError:
                    QMessageBox.warning(self, "Invalid Format", "Please enter time in HH:MM:SS format.")
        elif column == 3:  # End Time
            new_value, ok = QInputDialog.getText(
                self, f'Edit {column_name}',
                f'Enter new end time (HH:MM:SS):',
                text=current_task.get('end_time', '')
            )
            if ok and new_value.strip():
                try:
                    from datetime import datetime
                    datetime.strptime(new_value, '%H:%M:%S')
                    if self.db.update_task(task_id, current_task.get('title'), current_task.get('description'),
                                         current_task.get('start_date'), current_task.get('end_date'),
                                         current_task.get('start_time'), new_value):
                        QMessageBox.information(self, "Success", "End time updated successfully!")
                        self.refresh_table()
                    else:
                        QMessageBox.warning(self, "Error", "Failed to update end time.")
                except ValueError:
                    QMessageBox.warning(self, "Invalid Format", "Please enter time in HH:MM:SS format.")
        elif column == 4:  # Duration
            QMessageBox.information(self, "Edit Duration", "Duration is calculated automatically from start and end times.")
        elif column == 5:  # Status
            options = ["Not Yet", "Finished"]
            current_status = current_task.get('status', 'Not Yet')
            new_status, ok = QInputDialog.getItem(
                self, 'Edit Status',
                'Select new status:',
                options, options.index(current_status) if current_status in options else 0, False
            )
            if ok:
                if self.db.update_task_status(task_id, new_status):
                    QMessageBox.information(self, "Success", "Status updated successfully!")
                    self.refresh_table()
                else:
                    QMessageBox.warning(self, "Error", "Failed to update status.")
        elif column == 6:  # Actions
            QMessageBox.information(self, "Actions", "Click the Delete button to remove this task.")
    
    def delete_task(self, task_id):
        if task_id is None:
            QMessageBox.warning(self, "Error", "Invalid task ID.")
            return
            
        try:
            reply = QMessageBox.question(
                self, 'Delete Task',
                'Are you sure you want to delete this task?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.db.delete_task(task_id):
                    QMessageBox.information(self, "Success", "Task deleted successfully!")
                    self.refresh_table()
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete task.")
        except Exception as e:
            print(f"Error deleting task: {e}")
            QMessageBox.warning(self, "Error", f"Failed to delete task: {str(e)}")
    
    def refresh_table(self):
        try:
            self.load_data()
        except Exception as e:
            print(f"Error refreshing table: {e}")
            self.populate_table([])
    
    def export_to_csv(self):
        if not self.current_tasks:
            QMessageBox.information(self, "No Data", "No activities to export.")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, 'Export to CSV', 
            f'trackerin_activities_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            'CSV Files (*.csv)'
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    
                    headers = ['ID', 'Title', 'Description', 'Start Date', 'End Date', 
                             'Start Time', 'End Time', 'Status', 'Created At']
                    writer.writerow(headers)
                    
                    for task in self.current_tasks:
                        row = [
                            task['id'],
                            task['title'],
                            task['description'],
                            task['start_date'],
                            task['end_date'],
                            task['start_time'],
                            task['end_time'],
                            task['status'],
                            task.get('created_at', '')
                        ]
                        writer.writerow(row)
                
                QMessageBox.information(self, "Success", f"Data exported successfully to:\n{filename}")
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to export data:\n{str(e)}")
    
    def update_profile(self):
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        student_id = self.id_input.text().strip()
        status_type = self.status_combo.currentText()
        
        if not name:
            QMessageBox.warning(self, "Warning", "Please enter your full name.")
            return
        
        if self.db.update_user_profile(name, email, student_id, status_type):
            QMessageBox.information(self, "Success", "Profile updated successfully!")
            self.profile_updated.emit()
        else:
            QMessageBox.warning(self, "Error", "Failed to update profile.")
    
    def change_profile_picture(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, 'Select Profile Picture',
            '', 'Image Files (*.png *.jpg *.jpeg *.gif *.bmp)'
        )
        
        if filename:
            try:
                assets_dir = "assets"
                if not os.path.exists(assets_dir):
                    os.makedirs(assets_dir)
                
                import shutil
                file_extension = os.path.splitext(filename)[1]
                new_filename = os.path.join(assets_dir, f"profile_pic_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}")
                shutil.copy2(filename, new_filename)
                
                profile_data = self.db.get_user_profile()
                if profile_data:
                    success = self.update_user_profile_picture(new_filename)
                    if success:
                        profile_image = self.load_profile_image(new_filename)
                        if isinstance(profile_image, QPixmap):
                            self.profile_pic_frame.setPixmap(profile_image)
                            self.profile_pic_frame.setText("") 
                        else:
                            self.profile_pic_frame.setText(profile_image)
                        
                        QMessageBox.information(self, "Success", f"Profile picture updated successfully!")
                        self.profile_updated.emit()
                    else:
                        QMessageBox.warning(self, "Error", "Failed to update profile picture in database.")
                else:
                    QMessageBox.warning(self, "Error", "No user profile found.")
                    
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to update profile picture:\n{str(e)}")
    
    def update_user_profile_picture(self, picture_path):
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE user_profile 
                    SET profile_picture = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = (SELECT MAX(id) FROM user_profile)
                ''', (picture_path,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error updating profile picture: {e}")
            return False
    
    def show_filter_options(self):
        options = ["All Tasks", "Completed Only", "Pending Only", "Today's Tasks"]
        item, ok = QInputDialog.getItem(self, "Filter Options", "Select filter:", options, 0, False)
        
        if ok:
            if item == "Completed Only":
                filtered_tasks = [task for task in self.current_tasks if task['status'] == 'Finished']
            elif item == "Pending Only":
                filtered_tasks = [task for task in self.current_tasks if task['status'] == 'Not Yet']
            elif item == "Today's Tasks":
                today = datetime.now().strftime('%Y-%m-%d')
                filtered_tasks = [task for task in self.current_tasks if task['start_date'] == today]
            else:
                filtered_tasks = self.current_tasks
            
            self.populate_table(filtered_tasks)
    
    def paste_to_active_input(self, text):
        focused_widget = QApplication.focusWidget()
        
        if isinstance(focused_widget, QLineEdit):
            if focused_widget == self.search_input:
                focused_widget.setText(text)
                QMessageBox.information(self, "Clipboard", "Text pasted to search box!")
            elif hasattr(self, 'name_input') and focused_widget == self.name_input:
                focused_widget.setText(text)
                QMessageBox.information(self, "Clipboard", "Text pasted to name field!")
            elif hasattr(self, 'email_input') and focused_widget == self.email_input:
                focused_widget.setText(text)
                QMessageBox.information(self, "Clipboard", "Text pasted to email field!")
            elif hasattr(self, 'id_input') and focused_widget == self.id_input:
                focused_widget.setText(text)
                QMessageBox.information(self, "Clipboard", "Text pasted to student ID field!")
            else:
                focused_widget.setText(text)
                QMessageBox.information(self, "Clipboard", "Text pasted to input field!")
        else:
            self.search_input.setFocus()
            self.search_input.setText(text)
            QMessageBox.information(self, "Clipboard", "Text pasted to search box!")
