import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseHandler:
    def __init__(self, db_path: str = "trackerin.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    start_date DATE NOT NULL,
                    end_date DATE,
                    start_time TIME NOT NULL,
                    end_time TIME NOT NULL,
                    status TEXT DEFAULT 'Not Yet',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fullname TEXT NOT NULL,
                    email TEXT,
                    student_id TEXT,
                    status_type TEXT DEFAULT 'Student',
                    profile_picture TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('SELECT COUNT(*) FROM user_profile')
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO user_profile (fullname, email, student_id, status_type)
                    VALUES (?, ?, ?, ?)
                ''', ("Demo User", "demo@example.com", "", "User"))
            
            conn.commit()
    
    def add_task(self, title: str, description: str, start_date: str, end_date: str, 
                 start_time: str, end_time: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tasks (title, description, start_date, end_date, start_time, end_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (title, description, start_date, end_date, start_time, end_time))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error adding task: {e}")
            return False
    
    def get_tasks_by_date(self, date: str) -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, title, description, start_date, end_date, start_time, end_time, status
                    FROM tasks 
                    WHERE start_date = ? 
                    ORDER BY 
                        CASE status 
                            WHEN 'Finished' THEN 0 
                            ELSE 1 
                        END,
                        start_time
                ''', (date,))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error getting tasks: {e}")
            return []
    
    def get_all_tasks(self) -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, title, description, start_date, end_date, start_time, end_time, status, created_at
                    FROM tasks 
                    ORDER BY start_date DESC, start_time
                ''')
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error getting all tasks: {e}")
            return []
    
    def update_task_status(self, task_id: int, status: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tasks 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (status, task_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error updating task status: {e}")
            return False
    
    def update_task(self, task_id: int, title: str, description: str, start_date: str, 
                   end_date: str, start_time: str, end_time: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tasks 
                    SET title = ?, description = ?, start_date = ?, end_date = ?, 
                        start_time = ?, end_time = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (title, description, start_date, end_date, start_time, end_time, task_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error updating task: {e}")
            return False
    
    def delete_task(self, task_id: int) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error deleting task: {e}")
            return False
    
    def search_tasks(self, search_term: str) -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, title, description, start_date, end_date, start_time, end_time, status, created_at
                    FROM tasks 
                    WHERE title LIKE ? OR description LIKE ?
                    ORDER BY start_date DESC, start_time
                ''', (f'%{search_term}%', f'%{search_term}%'))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error searching tasks: {e}")
            return []
    
    def get_user_profile(self) -> Optional[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, fullname, email, student_id, status_type, profile_picture
                    FROM user_profile 
                    ORDER BY id DESC 
                    LIMIT 1
                ''')
                
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
        except sqlite3.Error as e:
            print(f"Error getting profile: {e}")
            return None
    
    def update_user_profile(self, fullname: str, email: str, student_id: str, status_type: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE user_profile 
                    SET fullname = ?, email = ?, student_id = ?, status_type = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = (SELECT MAX(id) FROM user_profile)
                ''', (fullname, email, student_id, status_type))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error updating profile: {e}")
            return False
    
    def update_user_profile_picture(self, picture_path: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE user_profile 
                    SET profile_picture = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = (SELECT MAX(id) FROM user_profile)
                ''', (picture_path,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error updating profile picture: {e}")
            return False
    
    def update_user_profile_with_picture(self, fullname: str, email: str, student_id: str, 
                                       status_type: str, picture_path: str = None) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if picture_path:
                    cursor.execute('''
                        UPDATE user_profile 
                        SET fullname = ?, email = ?, student_id = ?, status_type = ?, 
                            profile_picture = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = (SELECT MAX(id) FROM user_profile)
                    ''', (fullname, email, student_id, status_type, picture_path))
                else:
                    cursor.execute('''
                        UPDATE user_profile 
                        SET fullname = ?, email = ?, student_id = ?, status_type = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = (SELECT MAX(id) FROM user_profile)
                    ''', (fullname, email, student_id, status_type))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error updating profile with picture: {e}")
            return False
    
    def get_task_statistics(self) -> Dict:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total tasks
                cursor.execute('SELECT COUNT(*) FROM tasks')
                total_tasks = cursor.fetchone()[0]
                
                # Completed tasks
                cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = "Finished"')
                completed_tasks = cursor.fetchone()[0]
                
                # Pending tasks
                cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = "Not Yet"')
                pending_tasks = cursor.fetchone()[0]
                
                # Tasks today
                today = datetime.now().strftime('%Y-%m-%d')
                cursor.execute('SELECT COUNT(*) FROM tasks WHERE start_date = ?', (today,))
                today_tasks = cursor.fetchone()[0]
                
                return {
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'pending_tasks': pending_tasks,
                    'today_tasks': today_tasks
                }
        except sqlite3.Error as e:
            print(f"Error getting statistics: {e}")
            return {'total_tasks': 0, 'completed_tasks': 0, 'pending_tasks': 0, 'today_tasks': 0}
