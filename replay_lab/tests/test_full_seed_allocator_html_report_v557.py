from replay_lab.feedback.full_seed_allocator_html_report_v557 import FullSeedAllocatorHTMLReportV557


def test_full_seed_allocator_html_report_writes_latest():
    path = FullSeedAllocatorHTMLReportV557().build()
    assert path.exists()
    assert path.name == "latest_full_seed_allocator_report.html"
