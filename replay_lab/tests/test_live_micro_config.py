import json

import pytest

from live_data.live_micro_config import LiveMicroConfig, load_live_micro_config


def test_live_micro_config_defaults_real_order_disabled():
    cfg = LiveMicroConfig().validate()

    assert cfg.real_order_enabled is False


def test_live_micro_config_rejects_real_order_enabled():
    with pytest.raises(RuntimeError):
        LiveMicroConfig(real_order_enabled=True).validate()


def test_live_micro_config_loads_nested_json(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"forward_paper": {"fixed_order_krw": 20000}, "safety": {"real_order_enabled": False}}), encoding="utf-8")

    cfg = load_live_micro_config(path)

    assert cfg.fixed_order_krw == 20000
