import importlib


def test_build_cancel_params_includes_motive_and_optional_uuid():
    module = importlib.import_module(
        "erpnext_facturama.facturacionorcom.doctype.facturama_settings.facturama_settings"
    )

    params = module.build_cancel_params("cfdi-123", motive="01", uuid_replacement="uuid-999")

    assert params == {
        "motive": "01",
        "uuidReplacement": "uuid-999",
    }
