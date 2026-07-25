import tempfile
import unittest
from pathlib import Path

from database import DatabaseHandler


class DatabaseHandlerTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_directory.name) / "trackerin-test.db"
        self.database = DatabaseHandler(str(database_path))

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_default_profile_uses_generic_demo_data(self):
        profile = self.database.get_user_profile()

        self.assertEqual(profile["fullname"], "Demo User")
        self.assertEqual(profile["email"], "demo@example.com")
        self.assertEqual(profile["student_id"], "")
        self.assertEqual(profile["status_type"], "User")

    def test_task_lifecycle_and_statistics(self):
        created = self.database.add_task(
            "Write documentation",
            "Prepare the project README",
            "2026-07-26",
            "2026-07-26",
            "09:00:00",
            "10:00:00",
        )
        self.assertTrue(created)

        tasks = self.database.get_tasks_by_date("2026-07-26")
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["title"], "Write documentation")

        task_id = tasks[0]["id"]
        self.assertTrue(self.database.update_task_status(task_id, "Finished"))

        statistics = self.database.get_task_statistics()
        self.assertEqual(statistics["total_tasks"], 1)
        self.assertEqual(statistics["completed_tasks"], 1)

        self.assertTrue(self.database.delete_task(task_id))
        self.assertEqual(self.database.get_all_tasks(), [])

    def test_search_uses_parameterized_queries(self):
        self.database.add_task(
            "Portfolio review",
            "Review the desktop application",
            "2026-07-26",
            "2026-07-26",
            "11:00:00",
            "12:00:00",
        )

        self.assertEqual(len(self.database.search_tasks("Portfolio")), 1)
        self.assertEqual(self.database.search_tasks("' OR 1=1 --"), [])


if __name__ == "__main__":
    unittest.main()
