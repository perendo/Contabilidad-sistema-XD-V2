try:
    import defusedxml
    print(f"defusedxml version: {defusedxml.__version__}")
except ImportError:
    print("DEFUSEDXML_NOT_INSTALLED")
