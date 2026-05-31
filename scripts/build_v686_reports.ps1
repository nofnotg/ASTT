Set-Location "C:\ASTT"
python -m replay_lab.app.replay_cli run-v686-atr-ltf-coverage --initial-cash-krw 500000 --use-available-history true
python -m replay_lab.app.replay_cli run-v686-atr-ltf-replay --initial-cash-krw 500000 --use-available-history true
python -m replay_lab.app.replay_cli run-v686-atr-precision-v2 --initial-cash-krw 500000 --use-available-history true
python -m replay_lab.app.replay_cli run-v686-bear-window-atr-replay --initial-cash-krw 500000 --use-available-history true
python -m replay_lab.app.replay_cli register-v686-shadow-routes
python -m replay_lab.app.replay_cli run-v686-paper-backfill-with-v685-router --initial-cash-krw 500000 --start-date 2026-01-01
python -m replay_lab.app.replay_cli build-v686-local-dashboard-report-html
