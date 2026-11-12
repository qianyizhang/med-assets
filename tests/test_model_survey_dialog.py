"""Source contract only; native focus return still requires browser verification."""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] /
          'sites/model-survey/app/src/content/report/ReportContent.jsx').read_text()
DIALOG = SOURCE.split('function PreviewDialog(', 1)[1].split('\nfunction Media(', 1)[0]


class PreviewDialogLifecycleTests(unittest.TestCase):
    def test_state_is_cleared_on_close_not_cancel(self):
        self.assertIn('onClose={onClose}', DIALOG)
        self.assertNotIn('onCancel=', DIALOG)
        self.assertNotIn('onClick={onClose}', DIALOG)

    def test_explicit_dismissals_use_native_close(self):
        self.assertIn('aria-label="Close preview" onClick={()=>ref.current.close()}', DIALOG)
        self.assertIn('if(e.target===e.currentTarget)ref.current.close();', DIALOG)
        self.assertNotIn('onClose();', DIALOG)


if __name__ == '__main__':
    unittest.main()
